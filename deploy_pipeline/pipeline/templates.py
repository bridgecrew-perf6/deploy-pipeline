import os
from jinja2.environment import Environment, Template
from jinja2.exceptions import TemplateNotFound
from jinja2.loaders import BaseLoader
from jinja2.utils import select_autoescape


def get_template(template_path: str) -> Template:
    # init jinja environment
    return Environment(
        loader=FullPathLoader(),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    ).get_template(template_path)


# implement a loader that is capable of loading a template using an absolute path
class FullPathLoader(BaseLoader):
    def get_source(self, environment, template):
        # ensure the file exists
        if not os.path.exists(template):
            raise TemplateNotFound(template)

        # modified time
        mtime = os.path.getmtime(template)

        # open the file (in binary mode)
        with open(template, "rb") as f:
            source = f.read().decode('utf-8')

        return source, template, lambda: mtime == os.path.getmtime(template)
