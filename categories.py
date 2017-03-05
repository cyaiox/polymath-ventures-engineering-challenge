import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, backref
from jinja2 import Environment, FileSystemLoader
from api import getCategories


PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(PATH + '/templates'),
    trim_blocks=False
)
database_file = 'ebay_categories.db'
Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'
    """
    This model will store the categories obtained from GetCategories eBay API
    """
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    is_auto_pay_enabled = Column(Boolean, default=False)
    is_best_offer_enabled = Column(Boolean, default=False)
    is_leaf_category = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey('category.id'), nullable=True)
    children = relationship('Category', backref=backref('parent', remote_side=id))

    def __init__(self, name=None, parent=None):
        self.name = name
        self.parent = parent


def generateDatabase(database_file):
    engine = create_engine('sqlite:///%s' % database_file)
    Base.metadata.create_all(engine)


def removeDatabase(database_file):
    os.remove(database_file)


def render_template(template_filename, context):
    return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)


def create_html(id, category):
    file_name = "%s.html" % id
    context = {
        'category': category
    }
    with open(file_name, 'w') as f:
        html = render_template('template.html', context)
        f.write(html)


def serializeChildren(node, category_serialized):
    for children in node.children:
        category_serialized['children'].append({
            'id': children.id,
            'name': children.name,
            'level': children.level,
            'leaf': children.is_leaf_category,
            'children': []
        })
        if children.children:
            serializeChildren(children, category_serialized['children'][len(category_serialized['children']) - 1])


def renderCategory(category_ID):
    engine = create_engine('sqlite:///%s' % database_file)
    Base.metadata.bind = engine
    DBSession = sessionmaker()
    DBSession.bind = engine
    session = DBSession()

    try:
        category = session.query(Category).get(category_ID)
        category_serialized = {
            'id': category.id,
            'name': category.name,
            'level': category.level,
            'leaf': category.is_leaf_category,
            'children': []
        }
        serializeChildren(category, category_serialized)
        create_html(category_ID, category_serialized)

    except:
        print("Error: The category ID not exist in our database!")


if __name__ == "__main__":
    if sys.argv[1] == '--rebuild':
        removeDatabase(database_file)
        generateDatabase(database_file)
        getCategories(Base, Category, database_file)

    elif sys.argv[1] == '--render':
        print("--render %s" % sys.argv[2])
        renderCategory(sys.argv[2])