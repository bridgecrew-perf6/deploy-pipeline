import os
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template


def get_template(template_path: str) -> Template:
    directory, name = os.path.split(template_path)

    # init jinja environment
    return Environment(
        loader=FileSystemLoader(directory),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    ).get_template(name)
