from django.contrib.contenttypes.models import ContentType
from django.template import (Library, Node, Template, TemplateSyntaxError, 
                             Variable, loader, RequestContext)

from django_comments_xtd.models import XtdComment


register = Library()


class XtdCommentCountNode(Node):
    """Store the number of XtdComments for the given list of app.models"""

    def __init__(self, as_varname, content_types):
        """Class method to parse get_xtdcomment_list and return a Node."""
        self.as_varname = as_varname
        self.qs = XtdComment.objects.for_content_types(content_types)

    def render(self, context):
        context[self.as_varname] = self.qs.count()
        return ''


def get_xtdcomment_count(parser, token):
    """
    Gets the comment count for the given params and populates the template
    context with a variable containing that value, whose name is defined by the
    'as' clause.

    Syntax::

        {% get_xtdcomment_count as [varname] for [app].[model] [[app].[model]] %}

    Example usage::

        {% get_xtdcomment_count as comments_count for blog.story blog.quote %}

    """
    tokens = token.contents.split()

    if tokens[1] != 'as':
        raise template.TemplateSyntaxError("2nd. argument in %r tag must be 'for'" % tokens[0])

    as_varname = tokens[2]

    if tokens[3] != 'for':
        raise template.TemplateSyntaxError("4th. argument in %r tag must be 'for'" % tokens[0])

    content_types = _get_content_types(tokens[4:])
    return XtdCommentCountNode(as_varname, content_types)


class BaseLastXtdCommentsNode(Node):
    """Base class to deal with the last N XtdComments for a list of app.model"""

    def __init__(self, count, content_types):
        """Class method to parse get_xtdcomment_list and return a Node."""
        self.qs = XtdComment.objects.for_content_types(content_types)[:count]


class RenderLastXtdCommentsNode(BaseLastXtdCommentsNode):

    def render(self, context):
        strlist = []
        for xtd_comment in self.qs:
            template_search_list = [
                "django_comments_xtd/%s/%s/comment.html" % (
                    xtd_comment.content_type.app_label, 
                    xtd_comment.content_type.model),
                "django_comments_xtd/%s/comment.html" % (
                    xtd_comment.content_type.app_label,),
                "django_comments_xtd/comment.html"
            ]
            strlist.append(loader.render_to_string(
                    template_search_list, {"comment": xtd_comment}, context))
        return ''.join(strlist)


class GetLastXtdCommentsNode(BaseLastXtdCommentsNode):

    def __init__(self, count, as_varname, content_types):
        super(GetLastXtdCommentsNode, self).__init__(count, content_types)
        self.as_varname = as_varname

    def render(self, context):
        context[self.as_varname] = self.qs
        return ''
        

def _get_content_types(tokens):
    content_types = []
    for token in tokens:
        try:
            app, model = token.split('.')
            content_types.append(
                ContentType.objects.get(app_label=app, model=model))
        except ValueError:
            raise template.TemplateSyntaxError(
                "Argument %s in %r must be in the format 'app.model'" % (
                    token, tagname))
        except ContentType.DoesNotExist:
            raise template.TemplateSyntaxError(
                "%r tag has non-existant content-type: '%s.%s'" % (
                    tagname, app, model))
    return content_types


def render_last_xtdcomments(parser, token):
    """
    Render the last N XtdComments through the 
      ``comments_xtd/comment.html`` template

    Syntax::

        {% render_last_xtdcomments [N] for [app].[model] [[app].[model]] %}

    Example usage::

        {% render_last_xtdcomments 5 for blog.story blog.quote %}

    """
    tokens = token.contents.split()

    try:
        count = int(tokens[1])
    except ValueError:
        raise template.TemplateSyntaxError(
            "Second argument in %r tag must be a integer" % tokens[0])

    if tokens[2] != 'for':
        raise template.TemplateSyntaxError(
            "Third argument in %r tag must be 'for'" % tokens[0])

    content_types = _get_content_types(tokens[3:])
    return RenderLastXtdCommentsNode(count, content_types)


def get_last_xtdcomments(parser, token):
    """
    Get the last N XtdComments

    Syntax::

        {% get_last_xtdcomments [N] as [varname] for [app].[model] [[app].[model]] %}

    Example usage::

        {% get_last_xtdcomments 5 as last_comments for blog.story blog.quote %}

    """
    tokens = token.contents.split()

    try:
        count = int(tokens[1])
    except ValueError:
        raise template.TemplateSyntaxError(
            "Second argument in %r tag must be a integer" % tokens[0])

    if tokens[2] != 'as':
        raise template.TemplateSyntaxError(
            "Third argument in %r tag must be 'as'" % tokens[0])

    as_varname = tokens[3]

    if tokens[4] != 'for':
        raise template.TemplateSyntaxError(
            "Fifth argument in %r tag must be 'for'" % tokens[0])

    content_types = _get_content_types(tokens[5:])
    return GetLastXtdCommentsNode(count, as_varname, content_types)


register.tag(get_xtdcomment_count)
register.tag(render_last_xtdcomments)
register.tag(get_last_xtdcomments)
