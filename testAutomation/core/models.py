from django.utils.translation import ugettext_lazy as _
from feincms.content.richtext.models import RichTextContent
from feincms.content.section.models import SectionContent
from feincms.module.medialibrary.contents import MediaFileContent
from feincms.module.page.models import Page


TYPE_CHOICES = (
    ('block', _('Block')),
    ('left', _('Left')),
    ('right', _('Right')),
)


SECTION_TYPE_CHOICES = (
    ('half', _('Half Width')),
    ('img-right', _('Full Width Image Right')),
    ('list-block', _('List Block')),
)


Page.register_templates(
    {
        'key': '1col',
        'title': 'Single column',
        'path': 'base.html',
        'regions': (
            ('main', _('Main content')),
            ('footer', _('Footer content')),
        ),
    },
    {
        'key': '2col',
        'title': 'Two columns',
        'path': 'page/2col.html',
        'regions': (
            ('main', _('Main content')),
            ('footer', _('Footer content')),
        ),
    },
)
Page.create_content_type(RichTextContent)
Page.create_content_type(MediaFileContent, TYPE_CHOICES=TYPE_CHOICES)
Page.create_content_type(SectionContent, TYPE_CHOICES=TYPE_CHOICES)
Page.register_extensions(
    'feincms.module.extensions.translations',
)
