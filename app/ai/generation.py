import json
import logging

import google.genai as genai
from app.database import conn, products
import app.env as env

_LOGGER = logging.getLogger(__name__)

client = genai.Client(api_key=env.GEMINI_KEY)


def generate_product_context_batch(product_names: list[str]) -> dict:
    prompt = f"""
    Com base em um lista de nomes de produtos provenientes de datasets da CONAB, ou seja, produtos do agronecio, como
    carnes, vegetais, frutas, hortaliças, grãos e entre outros.

    Faça o nome de apresentação do produto:
    - Os produtos do dataset estão normalizados, sem acentos e símbolos
    - Faça a versão deles capitalizadas e com os acentos para apresentação e identificação

    Os nomes dos produtos são: {", ".join(product_names)}

    Retorne um JSON:
    - Não mande um bloco markdown ou nada do tipo
    - Quero o JSON puro e sem pretty print
    - Utilize a seguinte estrutura:
    - As chaves referentes ao nome do produto no json devem ser exatamente iguais as chaves passadas na lista de produtos
    {{
        "product_name": {{
            "presentation_name": "...",
        }}
    }}
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
    )

    return json.loads(response.text)


def run_batch_update():
    _LOGGER.info("Starting batch update for product context")
    products_to_update = products.get_products_without_presentation_name(limit=20)

    if not products_to_update:
        _LOGGER.info("No products to update.")
        return

    product_names = [p["name"] for p in products_to_update]
    generated_data = generate_product_context_batch(product_names)

    db_conn = conn.get_db()
    try:
        db_conn.begin()
        for product in products_to_update:
            product_id = product["id"]
            product_name = product["name"]
            if product_name in generated_data:
                data = generated_data[product_name]
                _LOGGER.info(data)
                products.update_product_context(
                    db_conn,
                    product_id,
                    data["presentation_name"],
                )
        db_conn.commit()
        _LOGGER.info(f"Successfully updated {len(products_to_update)} products.")
    except Exception as e:
        db_conn.rollback()
        _LOGGER.error(f"Error updating products: {e}")
    finally:
        db_conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_batch_update()
