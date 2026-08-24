#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

# src/core/question_handlers/select_handler.py
import random

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from config.personal import personal_data
from config.questions import questions_data
from config.settings import settings_data
from src.core.question_handlers.base_handler import BaseQuestionHandler
from src.utils.logger import logger


class SelectHandler(BaseQuestionHandler):
    def can_handle(self, question_element):
        return self.scraper.interactor.try_xpath('.//select', click=False, element=question_element)

    def handle(self, question_element, job_description):
        select_element = self.scraper.interactor.try_xpath('.//select', click=False, element=question_element)
        select_obj = Select(select_element)

        label_element = self.scraper.interactor.try_xpath('.//label', click=False, element=question_element)
        try:
            label_text = label_element.find_element(By.TAG_NAME, "span").text
        except:
            label_text = label_element.text if label_element else "Unknown"

        label_lower = label_text.lower()
        selected_option = select_obj.first_selected_option.text
        options_text = [option.text for option in select_obj.options]

        unselected_placeholders = [
            "select an option", "selecionar opção", "selecione uma opção",
            "selecionar", "selecione", "select", "seleccionar una opción",
            "seleccionar", ""
        ]
        
        is_unselected = (
            selected_option.strip().lower() in unselected_placeholders
            or not select_obj.first_selected_option.get_attribute("value")
            or select_obj.first_selected_option.get_attribute("value").strip() == ""
        )

        valid_options = [
            opt.text.strip() for opt in select_obj.options
            if opt.text.strip() and opt.text.strip().lower() not in unselected_placeholders
        ]

        answer = 'Yes'
        prev_answer = selected_option

        if settings_data.overwrite_previous_answers or is_unselected:
            # Match Exact Conditions
            if any(term in label_lower for term in ['email', 'phone', 'telefone', 'celular']):
                answer = prev_answer
            elif any(term in label_lower for term in ['gender', 'sex', 'gênero', 'genero', 'sexo']):
                answer = personal_data.gender
            elif any(term in label_lower for term in ['disability', 'deficiência', 'deficiencia', 'pcd']):
                answer = personal_data.disability_status
            elif any(term in label_lower for term in ['proficiency', 'proficiência', 'proficiencia', 'nivel', 'nível']):
                answer = 'Professional'
            elif any(term in label_lower for term in ['experience', 'experiência', 'experiencia']):
                if any(term in label_lower for term in ['years', 'anos']):
                    answer = str(questions_data.years_of_experience)
                elif any(term in label_lower for term in ['additional months', 'meses']):
                    answer = str(questions_data.additional_months_of_experience)
            elif any(loc_word in label_lower for loc_word in ['location', 'city', 'state', 'country', 'cidade', 'estado', 'país', 'pais', 'localização', 'localizacao']):
                if 'country' in label_lower or 'país' in label_lower or 'pais' in label_lower:
                    answer = personal_data.country
                elif 'state' in label_lower or 'estado' in label_lower:
                    answer = personal_data.state
                elif 'city' in label_lower or 'cidade' in label_lower:
                    answer = personal_data.current_city
                else:
                    answer = personal_data.current_city
            elif any(term in label_lower for term in ['sponsorship', 'visa', 'visto', 'patrocínio', 'patrocinio']):
                answer = questions_data.require_visa
            elif 'personal relationship' in label_lower:
                answer = "no"
            elif 'shareholder' in label_lower:
                answer = "no"
            elif any(sal_w in label_lower for sal_w in ['salary', 'compensation', 'ctc', 'pay', 'salário', 'salario', 'remuneração', 'remuneracao', 'pretensão', 'pretensao']):
                if any(term in label_lower for term in ['current', 'present', 'atual']):
                    if any(term in label_lower for term in ['month', 'mês', 'mes']):
                        answer = str(round(questions_data.current_ctc / 12))
                    elif 'lakh' in label_lower or 'lpa' in label_lower:
                        answer = str(round(questions_data.current_ctc / 100000))
                    else:
                        answer = str(questions_data.current_ctc)
                else:
                    if any(term in label_lower for term in ['month', 'mês', 'mes']):
                        answer = str(round(questions_data.desired_salary / 12, 2))
                    elif 'lakh' in label_lower or 'lpa' in label_lower:
                        answer = str(round(questions_data.desired_salary / 100000, 2))
                    else:
                        answer = str(questions_data.desired_salary)

            # Try to select the answer
            try:
                select_obj.select_by_visible_text(answer)
            except NoSuchElementException:
                # Fuzzy Matching Logic
                possible_answer_phrases = [answer, answer.lower(), answer.upper(),
                                           ''.join(c for c in answer if c.isalnum())]
                if answer == 'Decline' or 'recusar' in answer.lower() or 'prefiro' in answer.lower():
                    possible_answer_phrases += ["Decline", "not wish", "don't wish", "Prefer not", "not want", "Recusar", "Prefiro não", "Não desejo"]
                elif any(y in answer.lower() for y in ['yes', 'sim', 'agree', 'concordo']):
                    possible_answer_phrases += ["Yes", "Agree", "I do", "I have", "Sim", "Concordo", "Possuo", "Tenho"]
                elif any(n in answer.lower() for n in ['no', 'não', 'nao', 'disagree', 'discordo']):
                    possible_answer_phrases += ["No", "Disagree", "I don't", "I do not", "Não", "Nao", "Discordo", "Não possuo", "Não tenho"]

                found_option = False
                for phrase in possible_answer_phrases:
                    for option in valid_options:
                        if phrase.lower() in option.lower() or option.lower() in phrase.lower():
                            select_obj.select_by_visible_text(option)
                            answer = option
                            found_option = True
                            break
                    if found_option: break

                # AI Fallback
                if not found_option and self.ai:
                    try:
                        logger.info(f"Trying AI for dropdown question: {label_text}")

                        ai_answer = self.ai.get_answer(
                            question=label_text,
                            question_type="select",
                            job_description=job_description,
                            options=valid_options if valid_options else options_text
                        )

                        logger.info(f"AI returned: {ai_answer}")

                        if ai_answer:
                            # Exact match first
                            for option in valid_options:
                                if ai_answer.strip().lower() == option.strip().lower():
                                    select_obj.select_by_visible_text(option)
                                    answer = option
                                    found_option = True
                                    break

                            # Partial fuzzy match
                            if not found_option:
                                for option in valid_options:
                                    if (
                                            ai_answer.lower() in option.lower()
                                            or option.lower() in ai_answer.lower()
                                    ):
                                        select_obj.select_by_visible_text(option)
                                        answer = option
                                        found_option = True
                                        break

                    except Exception as e:
                        logger.error(f"AI dropdown answering failed: {e}")

                # Random Fallback if completely unknown
                if not found_option and len(valid_options) > 0:
                    chosen = random.choice(valid_options)
                    logger.warning(f"Failed to find match for dropdown '{label_text}'. Selecting from valid options: {chosen}")
                    select_obj.select_by_visible_text(chosen)
                    answer = select_obj.first_selected_option.text

        return (label_text, select_obj.first_selected_option.text, "select")
