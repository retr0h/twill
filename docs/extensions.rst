.. _extensions:

=======================
twill Extension Modules
=======================

.. contents::

Several different extension modules are distributed with twill, under
'twill.extensions'.

check_links -- a simple link checker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A simple link checker is included with twill. To use it, do ::

   go <page>

   extend_with check_links
   check_links

'check_links' will visit each link on the current page and verify that
the HTTP status code is 200 (success). A list of failing links will be
printed out at the end of the function.

The 'check_links' function takes an optional argument, a regex to filter
for links that should be checked. By default the filter matches everything;
if you only wanted to check links on e.g. idyll.org, you could do ::

   go http://idyll.org/
   check_links .*\.idyll\.org

A few notes:

  * 'follow' is used to visit each link, so the referrer URL should
    be set correctly.

  * HTTP basic authentication and cookies work as you'd expect, so you
    can set up twill with all of the permissions necessary to visit restricted
    links & only then run check_links.

match_parse -- extension for regular expressions with multiple matches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The 'match_parse' extension module contains a number of functions for
dealing with multiple matches, etc. Here's some example code: ::

   extend_with match_parse
   go http://www.idyll.org/

   split "org"
   echo __matchlist__

   findall "t."
   echo __matchlist__

   split "org"
   popmatch 0
   getmatch test 'm[0].split()'
   showvar test

   split "org"
   setmatch "m.split()[0]"

   popmatch 0
   echo __matchlist__
   echo __match__

require -- assert that specific conditions hold after each page is loaded
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The 'require' extension module contains four functions that let you
assert specific conditions. For example, ::

   extend_with require
   require success

will assert that after each page load, the HTTP code is 200 ("success").
'require' does nothing on a 'back' call (which doesn't actually reload
a page).

Currently there are only two assertions available, 'success' and
'links_ok'. 'links_ok' automatically runs 'check_links' (see above) after
each page is loaded. 'links_ok' will not check links twice unless
you call 'flush_visited' (see below).

The other functions in this module are:

**skip_require** -- don't check the requirements for the next action.

**no_require** -- turn off requirements checking & reset conditions.

**flush_visited** -- flush the list of visited links.

mailman_sf -- discard spam messages from your SourceForge mailing lists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The 'mailman_sf' extension module contains two functions, 'discard_all_messages'
and 'exit_if_empty'. Here's some example code: ::

  # load in the mailman_sf extensions module
  extend_with mailman_sf

  # unfortunately we have to hard-code in the mailing list name for
  # the moment. not sure how to do substitutions here.
  go https://lists.sourceforge.net/lists/admindb/pywx-announce

  # fill out the page with the list password.
  getpassword "Enter list password: "
  formvalue 1 adminpw __password__
  submit 0
  code 200

  # if there aren't any messages on the page, exit.
  exit_if_empty

  # if not empty, discard all messages & submit
  discard_all_messages
  submit 0

argparse -- pass arguments into twill scripts via sys.argv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The 'argparse' extension module contains one function, 'get_args'. 'get_args'
loads all of the post-scriptfile command-line arguments into variables, e.g. ::

   $ twill script1 script2 script3 -- val1 val2 val3
   ...
   >> extend_with argparse
   >> get_args
   >> echo "args are ${arg1} ${args} ${arg3}"
   args are val1 val2 val3

dns_check -- make assertions about domain name service records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dns_check implements functions to test domain name service (DNS) resolution.
You'll need dnspython_ to use it.

Functions:

  * dns_resolves -- assert that a host resolves to a specific IP address.
  * dns_a -- assert that a host directly resolves to a specific IP address
  * dns_cname -- assert that a host is an alias for another hostname.
  * dnx_mx -- assert that a given host is a mail exchanger for the given name.
  * dns_ns -- assert that a given hostname is a name server for the given name.

.. _dnspython: http://www.dnspython.org/

csv_iterate -- iterate over lists of values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

csv_iterate provides a single function, 'csv_iterate', that lets you
run a script once for each row in a file of comma-separated values.
For example, if you had a file 'test.csv' containing ::

   value1, value2
   value3, value4

and a script 'test' containing ::

   echo "first value is ${col1}, second is ${col2}"

then ::

   >> csv_iterate test.csv test

would produce ::

   first value is value1, second is value2
   first value is value3, second is value4

This is designed for building test suites containing many different
combinations of values for specific forms.

dirstack -- manipulate the current working directory (cwd)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

dirstack provides two functions, 'chdir' and 'popd', which change the
directory and recover the original directory, respectively. The cwd
is kept in the global variable '__dir__'.

For example ::

   >> chdir /tmp
   >> echo __dir__
   >> popd
   >> echo __dir__

will change to the '/tmp' directory, print out '/tmp', and then change
back to the original directory.

formfill -- convenience functions for filling out forms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

formfill provides three functions, 'fv_match', 'fv_multi', and
'fv_multi_sub'.

'fv_match' allows you to set many form fields all at once, based
on regex matching to the form field name, e.g. ::

   fv_match <form> test-(\d+) 'hello world!'

will set all fields with the name 'test-#' (# is any number) to 'hello world!'

'fv_multi' allows you to set many form fields at once, using a
more compact notation: ::

   fv_multi <form> field1=value1 field2=value2 ...

'fv_multi' uses the same field-matching convention that 'formvalue' uses:
it simply iterates over all arguments, splits at the first '=', and
runs 'formvalue' directly.

'fv_multi_sub' does the same thing as 'fv_multi' and then executes
'submit'.

(Thanks to Ben Bangert for the idea!)
