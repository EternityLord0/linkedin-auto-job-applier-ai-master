#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

from config.schema.personal_model import PersonalModel

# ==========================================
# INSTANTIATE YOUR DATA HERE
# ==========================================
personal_data = PersonalModel(
    first_name="Gabriel",
    middle_name="Henrique Vicentin",
    last_name="Caldeira",
    phone_number="17991528117",
    current_city="São José do Rio Preto, São Paulo, Brasil",
    street="Sebastião Rodrigues de Oliveira",
    state="São Paulo",
    zipcode="15204-116",
    country="Brazil",
    ethnicity="White",
    gender="Male",
    disability_status="No",
    veteran_status="No"
)
