# -*- coding: utf-8 -*-
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from vilt.docmanager import DocManager
import logging
import os

def create_document(career, subject, path_file):
    processed_docs = 'processed_docs'
    filename = secure_filename(path_file)
    career_dir = os.path.join(processed_docs, career)
    destination_dir = os.path.join(career_dir, subject)
    if not os.path.exists(destination_dir):
        doc_manager = DocManager()
        doc_manager.create_new_career_dir(career, subject)

    dest_file = os.path.join(destination_dir, filename)
    if os.path.exists(dest_file):
        logging.info(f'The document has been previously processed.')
    else:
        file = FileStorage()
        file.save(dest_file)
        file.close()
        logging.info(f'The document {dest_file} has been successfully processed.')
    return dest_file


def delete_document(career, subject, document):
    deleted = False
    processed_docs = 'processed_docs'
    file_path = os.path.join(os.path.join(os.path.join(processed_docs, career), subject), document)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        deleted = True
        os.unlink(file_path)
    return deleted


if __name__ == '__main__':
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)
    selected_career = 'GCID'
    selected_subject = 'Inferencia Estadística'
    path_to_file = 'doc-test.pdf'
    destination_file = create_document(selected_career, selected_subject, path_to_file)
    if os.path.isfile(path_to_file):
        delete_document(selected_career, selected_subject, path_to_file)
        logging.info(f'The document {path_to_file} has been successfully deleted.')
