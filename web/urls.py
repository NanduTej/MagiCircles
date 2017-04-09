import string, inspect
from collections import OrderedDict
from django.conf.urls import include, patterns, url
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _, string_concat
from django.utils import timezone
#from web import bouncy # unused, only to force load the feedback process
from web import views_collections, magicollections
from web import views as web_views
from web.settings import RAW_CONTEXT, ENABLED_PAGES, ENABLED_NAVBAR_LISTS, SITE_NAME, EMAIL_IMAGE, GAME_NAME, SITE_DESCRIPTION, SITE_STATIC_URL, SITE_URL, GITHUB_REPOSITORY, SITE_LOGO, SITE_NAV_LOGO, JAVASCRIPT_TRANSLATED_TERMS, ACCOUNT_MODEL, STATIC_UPLOADED_FILES_PREFIX, COLOR, SITE_IMAGE, TRANSLATION_HELP_URL, DISQUS_SHORTNAME, HASHTAGS, TWITTER_HANDLE, EMPTY_IMAGE, GOOGLE_ANALYTICS, STATIC_FILES_VERSION, PROFILE_TABS, LAUNCH_DATE, PRELAUNCH_ENABLED_PAGES, NAVBAR_ORDERING
from web.utils import redirectWhenNotAuthenticated

views_module = __import__(settings.SITE + '.views', fromlist=[''])
try:
    custom_magicollections_module = __import__(settings.SITE + '.magicollections', fromlist=['']).__dict__
except ImportError:
    custom_magicollections_module = {}

############################################################
# Default enabled URLs (outside of collections + pages)

navbar_links = OrderedDict()

urls = [
    #url(r'^bouncy/', include('django_bouncy.urls', app_name='django_bouncy')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^password_reset[/]+$', 'django.contrib.auth.views.password_reset', {
        'template_name': 'password/password_reset_form.html',
        'html_email_template_name': 'password/password_reset_email_html.html',
        'from_email': settings.PASSWORD_EMAIL,

    }, name='password_reset'),
    url(r'^password_reset/done[/]+$', 'django.contrib.auth.views.password_reset_done', {
        'template_name': 'password/password_reset_done.html'
    }, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', 'django.contrib.auth.views.password_reset_confirm', {
        'template_name': 'password/password_reset_confirm.html'
    }, name='password_reset_confirm'),
    url(r'^reset/done[/]+$', 'django.contrib.auth.views.password_reset_complete', {
        'template_name': 'password/password_reset_complete.html'
    }, name='password_reset_complete'),
]

############################################################
# Navbar lists with dropdowns

def navbarAddLink(link_name, link, list_name=None):
    if list_name:
        if list_name not in navbar_links:
            navbar_links[list_name] = {
                'is_list': True,
                # show_link_callback gets added when links get ordered
            }
            navbar_links[list_name].update(ENABLED_NAVBAR_LISTS.get(list_name, {}))
            if 'title' not in navbar_links[list_name]:
                navbar_links[list_name]['title'] = _(string.capwords(list_name))
            if 'links' not in navbar_links[list_name]:
                navbar_links[list_name]['links'] = {}
        navbar_links[list_name]['links'][link_name] = link
    else:
        link['is_list'] = False
        navbar_links[link_name] = link

RAW_CONTEXT['all_enabled'] = []

############################################################
# URLs for collections

def getURLLambda(name, lambdas):
    return (lambda context: u'/{}/{}/'.format(name, '/'.join([f(context) for f in lambdas])))

def getCollectionShowLinkLambda(collection):
    return (lambda context: collection.list_view.has_permissions(context['request'], context))

collections = OrderedDict()

now = timezone.now()
launched = not LAUNCH_DATE or LAUNCH_DATE < now

disabled = []

for name, cls in custom_magicollections_module.items() + magicollections.__dict__.items():
    if name != 'MagiCollection' and inspect.isclass(cls) and issubclass(cls, magicollections.MagiCollection) and not name.startswith('_'):
        if cls.enabled and name not in disabled:
            collection = cls()
            if collection.name not in collections:
                collection.list_view = collection.ListView(collection)
                collection.item_view = collection.ItemView(collection)
                collection.add_view = collection.AddView(collection)
                collection.edit_view = collection.EditView(collection)
                if not launched:
                    for view in ['list', 'item', 'add', 'edit']:
                        getattr(collection, view + '_view').staff_required = True
                collections[collection.name] = collection
                RAW_CONTEXT['all_enabled'].append(collection.name)
        else:
            disabled.append(name)

for collection in collections.values():
    parameters = {
        'name': collection.name,
        'collection': collection,
    }
    ajax_parameters = parameters.copy()
    ajax_parameters['ajax'] = True
    if collection.list_view.enabled:
        url_name = '{}_list'.format(collection.name)
        urls.append(url(r'^{}[/]*$'.format(collection.plural_name), views_collections.list_view, parameters, name=url_name))
        if collection.list_view.ajax:
            urls.append(url(r'^ajax/{}/$'.format(collection.plural_name), views_collections.list_view, ajax_parameters, name='{}_ajax'.format(url_name)))
        for shortcut_url in collection.list_view.shortcut_urls:
            shortcut_parameters = parameters.copy()
            shortcut_parameters['shortcut_url'] = shortcut_url
            urls.append(url(r'^{}[/]*$'.format(shortcut_url), views_collections.list_view, shortcut_parameters, name=url_name))
        if collection.navbar_link:
            link = {
                'url_name': url_name,
                'url': '/{}/'.format(collection.plural_name),
                'title': collection.navbar_link_title,
                'icon': collection.icon,
                'image': collection.image,
                'auth': (True, False) if collection.list_view.authentication_required else (True, True),
                'get_url': None,
                'show_link_callback': getCollectionShowLinkLambda(collection),
                'divider_before': collection.navbar_link_list_divider_before,
                'divider_after': collection.navbar_link_list_divider_after,
            }
            navbarAddLink(url_name, link, collection.navbar_link_list)
    if collection.item_view.enabled:
        url_name = '{}_item'.format(collection.name)
        urls.append(url(r'^{}/(?P<pk>\d+)[/]*$'.format(collection.name), views_collections.item_view, parameters, name=url_name))
        urls.append(url(r'^{}/(?P<pk>\d+)[/]*$'.format(collection.plural_name), views_collections.item_view, parameters, name=url_name))
        urls.append(url(r'^{}/(?P<pk>\d+)/[\w-]+[/]*$'.format(collection.name), views_collections.item_view, parameters, name=url_name))
        urls.append(url(r'^{}/(?P<pk>\d+)/[\w-]+[/]*$'.format(collection.plural_name), views_collections.item_view, parameters, name=url_name))
        if collection.item_view.ajax:
            urls.append(url(r'^ajax/{}/(?P<pk>\d+)/$'.format(collection.name), views_collections.item_view, ajax_parameters, name='{}_ajax'.format(url_name)))
        if collection.item_view.reverse_url:
            urls.append(url(r'^{}/(?P<reverse>[\w-]+)[/]*$'.format(collection.name), views_collections.item_view, parameters, name=url_name))
            urls.append(url(r'^{}/(?P<reverse>[\w-]+)[/]*$'.format(collection.plural_name), views_collections.item_view, parameters, name=url_name))
        for shortcut_url, pk in collection.item_view.shortcut_urls:
            shortcut_parameters = parameters.copy()
            shortcut_parameters['shortcut_url'] = shortcut_url
            shortcut_parameters['pk'] = pk
            urls.append(url(r'^{}[/]*$'.format(shortcut_url), views_collections.item_view, shortcut_parameters, name=url_name))
    if collection.add_view.enabled:
        url_name = '{}_add'.format(collection.name)
        if collection.types:
            urls.append(url(r'^{}/add/(?P<type>[\w_]+)[/]*$'.format(collection.plural_name), views_collections.add_view, parameters, name=url_name))
            if collection.add_view.ajax:
                urls.append(url(r'^ajax/{}/add/(?P<type>[\w_]+)[/]*$'.format(collection.plural_name), views_collections.add_view, ajax_parameters, name='{}_ajax'.format(url_name)))
            for shortcut_url, _type in collection.add_view.shortcut_urls:
                shortcut_parameters = parameters.copy()
                shortcut_parameters['shortcut_url'] = shortcut_url
                shortcut_parameters['type'] = _type
                urls.append(url(r'^{}[/]*$'.format(shortcut_url), views_collections.add_view, shortcut_parameters, name=url_name))
        else:
            urls.append(url(r'^{}/add[/]*$'.format(collection.plural_name), views_collections.add_view, parameters, name=url_name))
            if collection.AddView.ajax:
                urls.append(url(r'^ajax/{}/add[/]*$'.format(collection.plural_name), views_collections.add_view, ajax_parameters, name='{}_ajax'.format(url_name)))
            for shortcut_url in collection.add_view.shortcut_urls:
                shortcut_parameters = parameters.copy()
                shortcut_parameters['shortcut_url'] = shortcut_url
                urls.append(url(r'^{}[/]*$'.format(shortcut_url), views_collections.add_view, shortcut_parameters, name=url_name))
    if collection.edit_view.enabled:
        url_name = '{}_edit'.format(collection.name)
        urls.append(url(r'^{}/edit/(?P<pk>\d+)/$'.format(collection.plural_name), views_collections.edit_view, parameters, name=url_name))
        if collection.edit_view.ajax:
            urls.append(url(r'^ajax/{}/edit/(?P<pk>\d+)/$'.format(collection.plural_name), views_collections.edit_view, ajax_parameters, name='{}_ajax'.format(url_name)))
        for shortcut_url, pk in collection.item_view.shortcut_urls:
            shortcut_parameters = parameters.copy()
            shortcut_parameters['shortcut_url'] = shortcut_url
            shortcut_parameters['pk'] = pk
            urls.append(url(r'^{}[/]*$'.format(shortcut_url), views_collections.item_view, shortcut_parameters, name=url_name))

############################################################
# URLs for pages

def getPageShowLinkLambda(page):
    return (lambda context: not (
        (page.get('authentication_required', False) and not context['request'].user.is_authenticated())
        or (page.get('logout_required', False) and context['request'].user.is_authenticated())
        or (page.get('staff_required', False) and not context['request'].user.is_staff))
    )

def page_view(name, page):
    function = (
        getattr(views_module, name)
        if page.get('custom', True)
        else getattr(web_views, name)
    )
    def _f(request, *args, **kwargs):
        if request.user.is_authenticated():
            if (page.get('logout_required', False)
                or (page.get('staff_required', False) and not request.user.is_staff)):
                raise PermissionDenied()
        elif page.get('authentication_required', False) or page.get('staff_required', False):
            redirectWhenNotAuthenticated(request, {
                'current_url': request.get_full_path() + ('?' if request.get_full_path()[-1] == '/' else '&'),
            }, next_title=page.get('title', ''))
        return function(request, *args, **kwargs)
    return _f

for (name, pages) in ENABLED_PAGES.items():
    if not isinstance(pages, list):
        pages = [pages]
    for page in pages:
        if not launched:
            if name not in PRELAUNCH_ENABLED_PAGES:
                page['staff_required'] = True
        if 'title' not in page:
            page['title'] = string.capwords(name)
        if not page.get('enabled', True):
            continue
        if name not in RAW_CONTEXT['all_enabled']:
            RAW_CONTEXT['all_enabled'].append(name)
        ajax = page.get('ajax', False)
        if name == 'index':
            urls.append(url(r'^$', page_view(name, page), name=name))
        else:
            url_variables = '/'.join(['(?P<{}>{})'.format(v[0], v[1]) for v in page.get('url_variables', [])])
            urls.append(url(r'^{}{}{}[/]*$'.format('ajax/' if ajax else '', name, '/' + url_variables if url_variables else ''),
                            page_view(name, page), name=name if not ajax else '{}_ajax'.format(name)))
        if not ajax:
            navbar_link = page.get('navbar_link', True)
            if navbar_link:
                lambdas = [(v[2] if len(v) >= 3 else (lambda x: x)) for v in page.get('url_variables', [])]
                link = {
                    'url_name': name,
                    'url': '/{}/'.format(name),
                    'title': page['title'],
                    'icon': page.get('icon', None),
                    'image': page.get('image', None),
                    'auth': page.get('navbar_link_auth', (True, True)),
                    'get_url': None if not page.get('url_variables', None) else (getURLLambda(name, lambdas)),
                    'show_link_callback': getPageShowLinkLambda(page),
                    'divider_before': page.get('divider_before', False),
                    'divider_after': page.get('divider_after', False),
                }
                navbarAddLink(name, link, page.get('navbar_link_list', None))

urlpatterns = patterns('', *urls)

############################################################
# Re-order navbar

order = [link_name for link_name in navbar_links.keys() if link_name not in NAVBAR_ORDERING] + NAVBAR_ORDERING

RAW_CONTEXT['navbar_links'] = OrderedDict((key, navbar_links[key]) for key in order if key in navbar_links)

for link_name, link in RAW_CONTEXT['navbar_links'].items():
    if link['is_list']:
        if link['links']:
            link['show_link_callback'] = lambda c: True
            if 'order' in link:
                order = [link_name for link_name in link['links'].keys() if link_name not in link['order']] + link['order']
                link['links'] = OrderedDict((key, link['links'][key]) for key in order if key in link['links'])
        else:
            link['show_link_callback'] = lambda c: False

############################################################
# Remove profile tabs when some collections are disabled

for collection_name in ['activity', 'badge', 'account']:
    if collection_name not in RAW_CONTEXT['all_enabled'] and collection_name in PROFILE_TABS:
        del(PROFILE_TABS[collection_name])

############################################################
# Set data in RAW_CONTEXT

RAW_CONTEXT['magicollections'] = collections
RAW_CONTEXT['account_model'] = ACCOUNT_MODEL
RAW_CONTEXT['site_name'] = SITE_NAME
RAW_CONTEXT['site_url'] = SITE_URL
RAW_CONTEXT['github_repository'] = GITHUB_REPOSITORY
RAW_CONTEXT['site_description'] = SITE_DESCRIPTION
RAW_CONTEXT['game_name'] = GAME_NAME
RAW_CONTEXT['static_uploaded_files_prefix'] = STATIC_UPLOADED_FILES_PREFIX
RAW_CONTEXT['static_url'] = SITE_STATIC_URL + 'static/'
RAW_CONTEXT['full_static_url'] = u'http:{}'.format(RAW_CONTEXT['static_url']) if 'http' not in RAW_CONTEXT['static_url'] else RAW_CONTEXT['static_url']
RAW_CONTEXT['site_logo'] = RAW_CONTEXT['static_url'] + 'img/' + SITE_LOGO if '//' not in SITE_LOGO else SITE_LOGO
RAW_CONTEXT['full_site_logo'] = u'http:{}'.format(RAW_CONTEXT['site_logo']) if 'http' not in RAW_CONTEXT['site_logo'] else RAW_CONTEXT['site_logo']
RAW_CONTEXT['site_nav_logo'] = SITE_NAV_LOGO
RAW_CONTEXT['disqus_shortname'] = DISQUS_SHORTNAME
RAW_CONTEXT['javascript_translated_terms'] = JAVASCRIPT_TRANSLATED_TERMS
RAW_CONTEXT['site_color'] = COLOR
RAW_CONTEXT['site_image'] = RAW_CONTEXT['static_url'] + 'img/' + SITE_IMAGE if '//' not in SITE_IMAGE else SITE_IMAGE
RAW_CONTEXT['full_site_image'] = u'http:{}'.format(RAW_CONTEXT['site_image']) if 'http' not in RAW_CONTEXT['site_image'] else RAW_CONTEXT['site_image']
RAW_CONTEXT['email_image'] = RAW_CONTEXT['static_url'] + 'img/' + EMAIL_IMAGE if '//' not in EMAIL_IMAGE else EMAIL_IMAGE
RAW_CONTEXT['full_email_image'] = u'http:{}'.format(RAW_CONTEXT['email_image']) if 'http' not in RAW_CONTEXT['email_image'] else RAW_CONTEXT['email_image']
RAW_CONTEXT['translation_help_url'] = TRANSLATION_HELP_URL
RAW_CONTEXT['hashtags'] = HASHTAGS
RAW_CONTEXT['twitter_handle'] = TWITTER_HANDLE
RAW_CONTEXT['empty_image'] = EMPTY_IMAGE
RAW_CONTEXT['full_empty_image'] = RAW_CONTEXT['static_url'] + 'img/' + RAW_CONTEXT['empty_image']
RAW_CONTEXT['google_analytics'] = GOOGLE_ANALYTICS
RAW_CONTEXT['static_files_version'] = STATIC_FILES_VERSION

if not launched:
    RAW_CONTEXT['launch_date'] = LAUNCH_DATE
