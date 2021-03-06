# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

if request.global_settings.web2py_version < "2.14.1":
    raise HTTP(500, "Requires web2py 2.13.3 or newer")

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# app configuration made easy. Look inside private/appconfig.ini
# -------------------------------------------------------------------------
from gluon.contrib.appconfig import AppConfig

# -------------------------------------------------------------------------
# once in production, remove reload=True to gain full speed
# -------------------------------------------------------------------------
myconf = AppConfig(reload=True)

if not request.env.web2py_runtime_gae:
    # ---------------------------------------------------------------------
    # if NOT running on Google App Engine use SQLite or other DB
    # ---------------------------------------------------------------------
    db = DAL(myconf.get('db.uri'),
             pool_size=myconf.get('db.pool_size'),
             migrate_enabled=myconf.get('db.migrate'),
             check_reserved=['all'])
else:
    # ---------------------------------------------------------------------
    # connect to Google BigTable (optional 'google:datastore://namespace')
    # ---------------------------------------------------------------------
    db = DAL('google:datastore+ndb')
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
# -------------------------------------------------------------------------
response.generic_patterns = ['*'] if request.is_local else []
# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = myconf.get('forms.formstyle')  # or 'bootstrap3_stacked' or 'bootstrap2' or other
response.form_label_separator = myconf.get('forms.separator') or ''

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = '0.0.0'

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

from gluon.tools import Auth, Service, PluginManager, Mail, Crud, prettydate
# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=myconf.get('host.names'))
service = Service()
plugins = PluginManager()
crud = Crud(db)
# -------------------------------------------------------------------------
# create all tables needed by auth if not custom tables
# -------------------------------------------------------------------------
auth.settings.extra_fields['auth_user']=[
    Field('profiletext','text'),
    Field('profileimage','upload', default='static/images/profile_default.png'),
    Field('votes', 'integer', default=0),
    ]
auth.define_tables(username=False, signature=False)
db.auth_user.votes.writable=False
db.auth_user.votes.readable=False
# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else myconf.get('smtp.server')
mail.settings.sender = myconf.get('smtp.sender')
mail.settings.login = myconf.get('smtp.login')
mail.settings.tls = myconf.get('smtp.tls') or False
mail.settings.ssl = myconf.get('smtp.ssl') or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table('mytable', Field('myfield', 'string'))
#
# Fields can be 'string','text','password','integer','double','boolean'
#       'date','time','datetime','blob','upload', 'reference TABLENAME'
# There is an implicit 'id integer autoincrement' field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield='value')
# >>> rows = db(db.mytable.myfield == 'value').select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)
crud.settings.auth = None


from datetime import datetime


# function to get the name of the user and put it in the table
def first_name():
    name = 'Nobody'
    if auth.user:
        name = auth.user.first_name
    return name

# function to get the email of the user and put it in the table
def get_email():
    email = ''
    if auth.user:
        email = auth.user.email
    return email

# define data access layer for reviews
reviewsdb = DAL('sqlite://storage.sqlite',
                auto_import=True
                )

# define the listing table we will be using
db.define_table('listing',
                Field('title'),
                Field('price', 'decimal(6,2)'),
                Field('sold', 'boolean'),
                Field('image', 'upload',default='static/images/No_image.png'),
                Field('name'),
                Field('user_id', db.auth_user),
                Field('phone'),
                Field('email'),
                Field('votes', 'integer', default=0),
                Field('messeged', 'text'),
                Field('date_posted', 'datetime'),
                )

# define the message table we will be using
db.define_table('private_messages',
                Field('fromid', db.auth_user, default=auth.user_id, readable=False, writable=False),
                Field('toid', db.auth_user, readable=False),
                Field('timesent', 'datetime', default=request.now, readable=False, writable=False),
                Field('subject', 'string', length=255),
                Field('messages','text'),
                Field('opened', 'boolean', writable=False, readable=False, default=False),
                Field('timeopened', 'datetime', readable=False, writable=False),
               )

# sets read / write priveleges
db.listing.votes.writable = False
db.listing.votes.readable = False
db.listing.user_id.writable = False
db.listing.user_id.readable = False
db.listing.name.writable = False
db.listing.date_posted.writable = False
db.listing.email.writable = False
db.listing.sold.default = False

# set the defaults for each variable
db.listing.messeged.label = 'Description'
db.listing.name.default = first_name()
db.listing.date_posted.default = datetime.utcnow()
db.listing.user_id.default = auth.user_id
db.listing.email.default = get_email()

# to check for proper price numbermesseged
db.listing.price.requires = IS_DECIMAL_IN_RANGE(0, 100000.00, dot=".")
#error_message='The price should be in the range 0..100000.00')

# to check for proper phone number using regular expr
db.listing.phone.requires = IS_MATCH('^1*?(\d{3}?|\(\d{3}\))\d{3}?\d{4}$',
                                    error_message='invalid phone number')
