"""
Various ugly utility functions for twill.

Apart from various simple utility functions, twill's robust parsing
code is implemented in the ConfigurableParsingFactory class.
"""

import os
import re

from lxml import etree, html, cssselect

try:
    import tidylib
except (ImportError, OSError):
    # ImportError can be raised when PyTidyLib package is not installed
    # OSError can be raised when the HTML Tidy shared library is not installed
    tidylib = None

from . import log
from errors import TwillException


class Singleton(object):
    """A mixin class to create singleton objects."""

    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        pass

    @classmethod
    def reset(cls):
        cls.__it__ = None


class ResultWrapper(object):
    """Deal with request results, and present them in a unified form.

    These objects are returned by browser._journey()-wrapped functions.
    """
    def __init__(self, req):
        self.req = req
        self.lxml = html.fromstring(self.req.text)
        orphans = self.lxml.xpath('//input[not(ancestor::form)]')
        if orphans:
            form = ['<form>']
            for orphan in orphans:
                form.append(etree.tostring(orphan))
            form.append('</form>')
            form = ''.join(form)
            self.forms = html.fromstring(form).forms
            self.forms.extend(self.lxml.forms)
        else:
            self.forms = self.lxml.forms

    @property
    def url(self):
        return self.req.url

    @property
    def http_code(self):
        return self.req.status_code

    @property
    def page(self):
        return self.req.text

    @property
    def headers(self):
        return self.req.headers

    @property
    def title(self):
        selector = cssselect.CSSSelector('title')
        return selector(self.lxml)[0].text

    @property
    def links(self):
        selector = cssselect.CSSSelector('a')
        return [(inner_tostring(a), a.get('href'))
                for a in selector(self.lxml)]

    def find_link(self, pattern):
        links = self.links
        search = re.search
        for link in links:
            if search(pattern, link[0]) or search(pattern, link[1]):
                return link[1]
        return ''

    def form(self, formname=1):
        forms = self.forms

        if not isinstance(formname, int):

            # first, try ID
            for form in forms:
                form_id = form.get('id')
                if form_id and form_id == formname:
                    return form

            # next, try regex with name
            regex = re.compile(formname)
            for form in forms:
                name = form.get('name')
                if name and regex.search(name):
                    return form

        # last, try number
        try:
            formnum = int(formname) - 1
            if not 0 <= formnum < len(forms):
                raise IndexError
        except (ValueError, IndexError):
            return None
        else:
            return forms[formnum]


def inner_tostring(element):
    """Serialize all the inner text and sub elements of the given element."""
    return '%s%s' % (
        element.text, ''.join(map(etree.tostring, element.getchildren())))


def trunc(s, length):
    """Truncate a string to a given length.

     The string is truncated by cutting off the last (length-4) characters
     and replacing them with ' ...'
    """
    if s and len(s) > length:
        return s[:length - 4] + ' ...'
    else:
        return s


def print_form(form, n):
    """Pretty-print the given form, with the assigned number."""
    info = log.info
    name = form.get('name')
    if name:
        info('\nForm name=%s (#%d)', name, n + 1)
    else:
        info('\nForm #%d', n + 1)

    if form.inputs is not None:
        info('## __Name__________________'
            ' __Type___ __ID________ __Value__________________')

        for n, field in enumerate(form.inputs):
            value = field.value
            if hasattr(field, 'value_options'):
                items = ', '.join("'%s'" % (
                    opt.name if hasattr(opt, 'name') else opt,)
                    for opt in field.value_options)
                value_displayed = '%s of %s' % (value, items)
            else:
                value_displayed = '%s' % (value,)
            field_name = field.name
            field_type = field.type if hasattr(field, 'type') else 'select'
            field_id = field.get('id')
            strings = (
                '%-2s' % (n + 1,),
                '%-24s %-9s' % (
                    trunc(field_name, 24), trunc(field_type, 9)),
                '%-12s' % (trunc(field_id, 12),),
                trunc(value_displayed, 40))
            info(' '.join(strings))
    info('')


def make_boolean(value):
    """Convert the input value into a boolean."""
    value = str(value).lower().strip()

    # true/false
    if value in ('true', 'false'):
        return value == 'true'

    # 0/nonzero
    try:
        ival = int(value)
    except ValueError:
        pass
    else:
        return bool(ival)

    # +/-
    if value in ('+', '-'):
        return value == '+'

    # on/off
    if value in ('on', 'off'):
        return value == 'on'

    raise TwillException("unable to convert '%s' into true/false" % (value,))


def set_form_control_value(control, value):
    """Set the given control to the given value

    The controls can be checkboxes, select elements etc.
    """
    if hasattr(control, 'type'):
        if control.type == 'checkbox':
            try:
                value = make_boolean(value)
            except TwillException:
                # if there's more than one checkbox,
                # it should be a html.CheckboxGroup, see below.
                pass
            else:
                control.checked = value

        elif control.type not in ('submit', 'image'):
            control.value = value
            
    elif isinstance(control, html.CheckboxGroup):
        if value.startswith('-'):
            value = value[1:]
            try:
                control.value.remove(value)
            except KeyError:
                pass
        else:
            if value.startswith('+'):
                value = value[1:]
            control.value.add(value)

    elif isinstance(control, html.SelectElement):
        # for ListControls (checkboxes, multiselect, etc.) we first need
        # to find the right *value*.  Then we need to set it +/-.
        # Figure out if we want to *select* it, or if we want to *deselect*
        # it.  By default (no +/-) select...
        if value.startswith('-'):
            add = False
            value = value[1:]
        else:
            add = True
            if value.startswith('+'):
                value = value[1:]

        # now, select the value.
        options = [opt.strip() for opt in control.value_options]
        option_names = [c.text.strip() for c in control.getchildren()]
        full_options = dict(zip(option_names, options))
        for name, opt in full_options.iteritems():
            if value not in (name, opt):
                continue
            if hasattr(control, 'checkable') and control.checkable:
                control.checked = add
            if add:
                control.value.add(opt)
                break
            else:
                try:
                    control.value.remove(opt)
                except ValueError:
                    pass
                break
        else:
            raise TwillException('Attempt to set an invalid value')

    else:
        raise TwillException('Attempt to set value on invalid control')


def _all_the_same_submit(matches):
    """Check if a list of controls all belong to the same control.

    For use with checkboxes, hidden, and submit buttons.
    """
    name = value = None
    for match in matches:
        if match.type not in ('submit', 'hidden'):
            return False
        if name is None:
            name = match.name
            value = match.value
        elif match.name != name or match.value != value:
                return False
    return True


def _all_the_same_checkbox(matches):
    """Check if a list of controls all belong to the same checkbox.

    Hidden controls can combine with checkboxes, to allow form
    processors to ensure a False value is returned even if user
    does not check the checkbox. Without the hidden control, no
    value would be returned.
    """
    name = None
    for match in matches:
        if match.type not in ('checkbox', 'hidden'):
            return False
        if name is None:
            name = match.name
        else:
            if match.name != name:
                return False
    return True


def unique_match(matches):
    """Check whether a match is unique"""
    return (len(matches) == 1 or
            _all_the_same_checkbox(matches) or _all_the_same_submit(matches))


def run_tidy(html):
    """Run HTML Tidy on the given HTML string.

    Return a 2-tuple (output, errors).  (None, None) will be returned if
    PyTidyLib (or the required shared library for tidy) isn't installed.
    """
    from .commands import options
    require_tidy = options.get('require_tidy')

    if not tidylib:
        if require_tidy:
            raise TwillException(
                'Option require_tidy is set, but PyTidyLib is not installed')
        return None, None
    
    clean_html, errors = tidylib.tidy_document(html)
    return clean_html, errors


def _is_valid_filename(f):
    """Check if the given filename is valid (not a backup file)."""
    return not f.endswith(('~', '.bak', '.old'))


def _follow_equiv_refresh():
    """Check if the browser shall ask whether to follow meta redirects."""
    from .commands import options
    return options.get('acknowledge_equiv_refresh')


def gather_filenames(arglist):
    """Collect script files from within directories."""
    names = []
    for arg in arglist:
        if os.path.isdir(arg):
            s = []
            for dirpath, dirnames, filenames in os.walk(arg):
                if dirpath in ('.git', '.hg', '.svn'):
                    continue
                for f in filenames:
                    if _is_valid_filename(f):
                        f = os.path.join(dirpath, f)
                        s.append(f)
            names.extend(sorted(s))
        else:
            names.append(arg)
    return names
