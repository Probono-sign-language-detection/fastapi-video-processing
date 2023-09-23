"""
schema : serialize 역활 담당
mongodb format json로의 변환
"""

def pdf_entity(db_item) -> dict:
    return {
        "id" : str(db_item["_id"]),
        "title" : str(db_item["press_title"]),
        "url" : str(db_item["press_url"]),
        "s3_uri" : str(db_item["press_pdf_s3_uri"]),
    }

def list_of_pdf_entity(db_item_list) -> list:
    list_pdf_entity = []
    for item in db_item_list:
        list_pdf_entity.append(pdf_entity(item))
    
    return list_pdf_entity

