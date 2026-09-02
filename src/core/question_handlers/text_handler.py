# src/core/question_handlers/text_handler.py
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from config.personal import personal_data
from config.questions import questions_data
from config.settings import settings_data
from src.core.question_handlers.base_handler import BaseQuestionHandler


class TextHandler(BaseQuestionHandler):
    def can_handle(self, question_element):
        return (self.scraper.interactor.try_xpath('.//input[@type="text"]', click=False, element=question_element) or
                self.scraper.interactor.try_xpath('.//textarea', click=False, element=question_element))

    def handle(self, question_element, job_description):
        # 1. Identify input type
        input_element = self.scraper.interactor.try_xpath('.//input[@type="text"]', click=False,
                                                          element=question_element)
        question_type = "text"
        if not input_element:
            input_element = self.scraper.interactor.try_xpath('.//textarea', click=False, element=question_element)
            question_type = "textarea"

        # 2. Extract Label
        label_element = self.scraper.interactor.try_xpath('.//label[@for]', click=False, element=question_element)
        try:
            hidden_label = label_element.find_element(By.CLASS_NAME, 'visually-hidden')
            label_text = hidden_label.text if hidden_label else label_element.text
        except:
            label_text = label_element.text if label_element else "Unknown"

        label_lower = label_text.lower()
        prev_answer = input_element.get_attribute("value")
        answer = ""
        do_actions = False

        # 3. Match Exact Conditions (PT & EN)
        if not prev_answer or settings_data.overwrite_previous_answers:
            # Textarea specifics
            if question_type == "textarea":
                if any(term in label_lower for term in ['summary', 'resumo', 'sobre você', 'sobre voce', 'bio', 'apresentação', 'apresentacao']):
                    answer = questions_data.linkedin_summary
                elif any(term in label_lower for term in ['cover', 'carta de apresentação', 'carta de apresentacao', 'carta de motivacao', 'carta de motivação']):
                    answer = questions_data.cover_letter

            # Standard Text Input specifics
            if answer == "":
                # Phone / Telefone / Celular
                if any(term in label_lower for term in ['phone', 'mobile', 'telefone', 'celular', 'whatsapp', 'contato']):
                    answer = personal_data.phone_number

                # Hourly rate / Valor Hora PJ (Check BEFORE monthly salary)
                elif any(term in label_lower for term in ['valor hora', 'valor/hora', 'taxa horária', 'taxa horaria', 'hourly rate', 'hourly', 'por hora']):
                    answer = "50"

                # Salary / Pretensão Salarial / Remuneração / Expectativa de Valor
                elif any(term in label_lower for term in ['salary', 'compensation', 'ctc', 'pay', 'salário', 'salario', 'salarial', 'remuneração', 'remuneracao', 'pretensão', 'pretensao', 'expectativa', 'modelo clt', 'valor clt', 'quanto pretende']):
                    if any(term in label_lower for term in ['current', 'present', 'atual', 'último', 'ultimo']):
                        if any(term in label_lower for term in ['month', 'mês', 'mes', 'mensal']):
                            answer = str(round(questions_data.current_ctc / 12, 2))
                        else:
                            answer = str(questions_data.current_ctc)
                    else:
                        if any(term in label_lower for term in ['month', 'mês', 'mes', 'mensal']):
                            answer = str(round(questions_data.desired_salary / 12, 2))
                        else:
                            answer = str(questions_data.desired_salary)

                # Years of Experience / Quanto tempo / Anos de experiência
                elif any(term in label_lower for term in ['experience', 'years', 'experiência', 'experiencia', 'quantos anos', 'quanto tempo', 'tempo de experiência', 'tempo de experiencia', 'tempo atua', 'tempo você trabalha', 'tempo voce trabalha', 'tempo de atuação', 'tempo de atuacao']):
                    base_years = int(questions_data.years_of_experience)
                    extra_year = 1 if questions_data.additional_months_of_experience >= 6 else 0
                    answer = str(base_years + extra_year)

                # Address / Street / Rua / Endereço
                elif any(term in label_lower for term in ['street', 'rua', 'endereço', 'endereco', 'logradouro']):
                    answer = personal_data.street

                # City / Location / Cidade / Localização
                elif any(term in label_lower for term in ['city', 'location', 'address', 'cidade', 'localização', 'localizacao', 'município', 'municipio']):
                    # Use clean city name for typeahead search
                    answer = "São José do Rio Preto"
                    do_actions = True

                # State / Estado
                elif any(term in label_lower for term in ['state', 'province', 'estado', 'uf']):
                    answer = personal_data.state

                # Postal / Zip / CEP
                elif any(term in label_lower for term in ['zip', 'postal', 'code', 'cep', 'código postal', 'codigo postal']):
                    answer = personal_data.zipcode

                # Country / País
                elif any(term in label_lower for term in ['country', 'país', 'pais', 'nacionalidade']):
                    answer = personal_data.country

                # Signature / Assinatura
                elif any(term in label_lower for term in ['signature', 'assinatura', 'assine']):
                    answer = personal_data.full_name

                # Name / Nome
                elif any(term in label_lower for term in ['name', 'nome']):
                    if any(term in label_lower for term in ['full', 'completo']):
                        answer = personal_data.full_name
                    elif any(term in label_lower for term in ['first', 'primeiro']):
                        answer = personal_data.first_name.strip()
                    elif any(term in label_lower for term in ['middle', 'do meio']):
                        answer = personal_data.middle_name.strip()
                    elif any(term in label_lower for term in ['last', 'sobrenome', 'último', 'ultimo']):
                        answer = personal_data.last_name.strip()
                    elif any(term in label_lower for term in ['employer', 'empresa', 'atual']):
                        answer = questions_data.recent_employer
                    else:
                        answer = personal_data.full_name

                # Notice period / Aviso prévio / Início
                elif any(term in label_lower for term in ['notice', 'can you join', 'aviso prévio', 'aviso previo', 'disponibilidade para início', 'disponibilidade de início']):
                    if any(term in label_lower for term in ['month', 'mês', 'mes']):
                        answer = str(questions_data.notice_period // 30)
                    elif any(term in label_lower for term in ['week', 'semana']):
                        answer = str(questions_data.notice_period // 7)
                    else:
                        answer = str(questions_data.notice_period)

                # Social / Links
                elif 'linkedin' in label_lower:
                    answer = questions_data.linkedIn
                elif 'github' in label_lower:
                    answer = questions_data.github
                elif any(term in label_lower for term in ['website', 'blog', 'portfolio', 'portfólio', 'link', 'site']):
                    answer = questions_data.website

                # Certifications / Certificados / Certificações
                elif any(term in label_lower for term in ['certificados', 'certificado', 'certificações', 'certificacoes', 'certificação', 'certificacao', 'certifications', 'certification']):
                    answer = "2"

                # Generic Count / Quantidade / Quantos / How many
                elif any(term in label_lower for term in ['quantos', 'quantas', 'how many', 'qual a quantidade', 'número de', 'numero de', 'quantidade de']):
                    if any(term in label_lower for term in ['projeto', 'projetos', 'projects']):
                        answer = "10"
                    elif any(term in label_lower for term in ['pessoa', 'pessoas', 'lider', 'time', 'equipe', 'team']):
                        answer = "5"
                    else:
                        answer = str(int(questions_data.years_of_experience))

                # Scales / Avaliações
                elif any(term in label_lower for term in ['scale of 1–10', 'scale of 1-10', '1 a 10', '1-10']):
                    answer = str(questions_data.confidence_level)
                elif any(term in label_lower for term in ['scale of 1–5', 'scale of 1-5', '1 a 5', '1-5']):
                    normalized = round((int(questions_data.confidence_level) / 10) * 5)
                    normalized = max(1, min(5, normalized))
                    answer = str(normalized)

                elif 'headline' in label_lower or 'título' in label_lower or 'titulo' in label_lower:
                    answer = questions_data.linkedin_headline
                elif any(term in label_lower for term in ['current company', 'empresa atual', 'onde trabalha']):
                    answer = questions_data.recent_employer

            # 4. Fallback to AI
            if answer == "" and self.ai and self.ai.is_active:
                answer = self.ai.get_answer(label_text, question_type, job_description)

            # 5. Foolproof Fallback: Never Leave Input Empty
            if not answer or str(answer).strip() == "":
                inp_type = input_element.get_attribute("type")
                inp_mode = input_element.get_attribute("inputmode")
                is_numeric = inp_type in ["number", "tel"] or inp_mode == "numeric" or any(term in label_lower for term in ['quant', 'how many', 'anos', 'tempo', 'número', 'numero', 'horas', 'hours'])

                if is_numeric:
                    answer = "4"
                elif any(term in label_lower for term in ['salár', 'salar', 'pretens', 'valor', 'remuner']):
                    answer = "8000"
                elif any(term in label_lower for term in ['sim', 'não', 'possui', 'experiência', 'conhecimento', 'desenvolveu', 'atuou']):
                    answer = "Sim"
                elif question_type == "text":
                    answer = "Sim"

            # 6. Execute Action safely (React-compatible input typing)
            if answer:
                answer_str = str(answer).strip()
                try:
                    input_element.click()
                    time.sleep(0.1)
                    input_element.send_keys(Keys.CONTROL + "a")
                    input_element.send_keys(Keys.BACKSPACE)
                    time.sleep(0.1)
                    input_element.send_keys(answer_str)
                except Exception:
                    try:
                        input_element.clear()
                        input_element.send_keys(answer_str)
                    except Exception:
                        pass

                if do_actions:
                    time.sleep(1.0)
                    # Try to click on the first typeahead autocomplete option
                    try:
                        suggestions = self.scraper.driver.find_elements(
                            By.XPATH,
                            "//div[contains(@class, 'basic-typeahead__selectable')] | //div[contains(@class, 'typeahead-suggestion')] | //li[contains(@class, 'basic-typeahead__selectable')] | //div[@role='option']"
                        )
                        if suggestions:
                            self.scraper.interactor.human_click(suggestions[0])
                        else:
                            self.scraper.actions.send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).send_keys(Keys.TAB).perform()
                    except Exception:
                        self.scraper.actions.send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).send_keys(Keys.TAB).perform()

        return (label_text, input_element.get_attribute("value"), question_type)

