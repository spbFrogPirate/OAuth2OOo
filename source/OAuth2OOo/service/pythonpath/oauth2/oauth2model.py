#!
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   Copyright (c) 2020 https://prrvchr.github.io                                     ║
║                                                                                    ║
║   Permission is hereby granted, free of charge, to any person obtaining            ║
║   a copy of this software and associated documentation files (the "Software"),     ║
║   to deal in the Software without restriction, including without limitation        ║
║   the rights to use, copy, modify, merge, publish, distribute, sublicense,         ║
║   and/or sell copies of the Software, and to permit persons to whom the Software   ║
║   is furnished to do so, subject to the following conditions:                      ║
║                                                                                    ║
║   The above copyright notice and this permission notice shall be included in       ║
║   all copies or substantial portions of the Software.                              ║
║                                                                                    ║
║   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,                  ║
║   EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES                  ║
║   OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.        ║
║   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY             ║
║   CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,             ║
║   TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE       ║
║   OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                    ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
"""

import uno
import unohelper

from com.sun.star.logging.LogLevel import INFO
from com.sun.star.logging.LogLevel import SEVERE

from com.sun.star.frame.DispatchResultState import SUCCESS

from com.sun.star.auth import RefreshTokenException

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_refresh_overlap
from .configuration import g_defaultlog
from .configuration import g_basename

from .unotool import generateUuid
from .unotool import getConfiguration
from .unotool import getCurrentLocale
from .unotool import getStringResource

from .logger import getLogger

from .wizard import WatchDog
from .wizard import Server

from .oauth2helper import getOAuth2ErrorCode

from requests.compat import urlencode
from requests import Session
from requests import ConnectionError
from requests import HTTPError
from six import string_types
import time
import validators
import base64
import hashlib
import json
from threading import Condition
import traceback


class OAuth2Model(unohelper.Base):
    def __init__(self, ctx, close=None, url='', user=''):
        self._ctx = ctx
        self._user = ''
        self._url = ''
        self._scope = ''
        self._provider = ''
        self._uuid = ''
        self._close = False
        self._uri = 'http://%s:%s/'
        self._urn = 'urn:ietf:wg:oauth:2.0:oob'
        self._watchdog = None
        self._logger = getLogger(ctx, g_defaultlog, g_basename)
        self._config = getConfiguration(ctx, g_identifier, True)
        self._resolver = getStringResource(ctx, g_identifier, g_extension)
        self._resources = {'Title': 'PageWizard%s.Title',
                           'Step': 'PageWizard%s.Step',
                           'UrlLabel': 'PageWizard1.Label4.Label',
                           'ProviderTitle': 'ProviderDialog.Title',
                           'ScopeTitle': 'ScopeDialog.Title',
                           'AuthorizationError': 'PageWizard3.Label2.Label',
                           'RequestMessage': 'PageWizard3.TextField1.Text.%s',
                           'TokenError': 'PageWizard4.Label2.Label',
                           'TokenLabel': 'PageWizard5.Label1.Label',
                           'TokenAccess': 'PageWizard5.Label6.Label',
                           'TokenRefresh': 'PageWizard5.Label4.Label',
                           'TokenExpires': 'PageWizard5.Label8.Label',
                           'DialogTitle': 'MessageBox.Title',
                           'DialogMessage': 'MessageBox.Message',
                           'UserTitle': 'UserDialog.Title',
                           'UserLabel': 'UserDialog.Label1.Label'}
        self.initialize(url, user, close)

    def initialize(self, url, user, close=None):
        self._initialize(url, user, close)

    def _initialize(self, url, user, close=None):
        self._user = user
        return self.initializeUrl(url, close)

    def initializeUrl(self, url, close=None):
        self._url = url
        configured, self._scope, self._provider = self._getUrlData(url)
        self._uuid = generateUuid()
        if close is not None:
            self._close = close
        return configured

    def _getUrlData(self, url):
        configured = False
        scope = provider = ''
        urls = self._config.getByName('Urls')
        if urls.hasByName(url):
            scope = urls.getByName(url).getByName('Scope')
            scopes = self._config.getByName('Scopes')
            if scopes.hasByName(scope):
                provider = scopes.getByName(scope).getByName('Provider')
                configured = True
        return configured, scope, provider

    @property
    def User(self):
        return self._user

    @property
    def Url(self):
        return self._url

    @property
    def ConnectTimeout(self):
        return self._config.getByName('ConnectTimeout')
    @ConnectTimeout.setter
    def ConnectTimeout(self, timeout):
        self._config.replaceByName('ConnectTimeout', timeout)

    @property
    def ReadTimeout(self):
        return self._config.getByName('ReadTimeout')
    @ReadTimeout.setter
    def ReadTimeout(self, timeout):
        self._config.replaceByName('ReadTimeout', timeout)

    @property
    def HandlerTimeout(self):
        return self._config.getByName('HandlerTimeout')
    @HandlerTimeout.setter
    def HandlerTimeout(self, timeout):
        self._config.replaceByName('HandlerTimeout', timeout)

    @property
    def Timeout(self):
        return self.ConnectTimeout, self.ReadTimeout

    @property
    def UrlList(self):
        return self._config.getByName('Urls').ElementNames

    def commit(self):
        if self._config.hasPendingChanges():
            self._config.commitChanges()

    def getProviderName(self, url):
        provider = ''
        if self._config.getByName('Urls').hasByName(url):
            scope = self._config.getByName('Urls').getByName(url).getByName('Scope')
            if self._config.getByName('Scopes').hasByName(scope):
                provider = self._config.getByName('Scopes').getByName(scope).getByName('Provider')
        return provider
 
    def dispose(self):
        self._cancelServer()

    def _cancelServer(self):
        if self._watchdog is not None:
            if self._watchdog.is_alive():
                self._watchdog.cancel()
                self._watchdog.join()
            self._watchdog = None

# OAuth2Model getter methods called by OptionsManager
    def getOptionsDialogData(self):
        return self.ConnectTimeout, self.ReadTimeout, self.HandlerTimeout, self.UrlList

# OAuth2Model getter methods called by OAuth2Handler
    def getUserData(self, url, msg):
        provider = self.getProviderName(url)
        title = self.getUserTitle(provider)
        label = self.getUserLabel(msg)
        return title, label

# OAuth2Model getter methods called by OAuth2Service
    def isAccessTokenExpired(self):
        providers = self._config.getByName('Providers')
        user = providers.getByName(self._provider).getByName('Users').getByName(self._user)
        if user.getByName('NeverExpires'):
            return False
        now = int(time.time())
        expire = max(0, user.getByName('TimeStamp') - now)
        return expire < g_refresh_overlap

    def getRefreshedToken(self):
        provider = self._config.getByName('Providers').getByName(self._provider)
        user = provider.getByName('Users').getByName(self._user)
        error = self._refreshToken(provider, user, False)
        if error is not None:
            raise self._getRefreshTokenException(error)
        return user.getByName('AccessToken')

    def _getRefreshTokenException(self, message):
        error = RefreshTokenException()
        error.Message = message
        error.ResourceUrl = self._url
        error.UserName = self._user
        return error

    def getToken(self):
        provider = self._config.getByName('Providers').getByName(self._provider)
        user = provider.getByName('Users').getByName(self._user)
        return user.getByName('AccessToken')

    def initializeSession(self, url, user):
        if self._initialize(url, user):
            return self.isAuthorized()
        return False

    def isAuthorized(self):
        providers = self._config.getByName('Providers')
        return self._isInitialized(providers) and self._isUrlScopeAuthorized(providers)

    def _isInitialized(self, providers):
        if providers.hasByName(self._provider):
            users = providers.getByName(self._provider).getByName('Users')
            return users.hasByName(self._user)
        return False

    def _isUrlScopeAuthorized(self, providers):
        scopes = self._config.getByName('Scopes')
        if scopes.hasByName(self._scope):
            values = providers.getByName(self._provider).getByName('Users').getByName(self._user).getByName('Scopes')
            for scope in scopes.getByName(self._scope).getByName('Values'):
                if scope not in values:
                    return False
            return True
        return False

# OAuth2Model getter methods called by WizardPages 1
    def getActivePath(self, user, url, provider, scope):
        urls = self._config.getByName('Urls')
        providers = self._config.getByName('Providers')
        if urls.hasByName(url) and self._isAuthorized(user, scope, provider, providers):
            path = 2
        elif providers.hasByName(provider) and not providers.getByName(provider).getByName('HttpHandler'):
            path = 1
        else:
            path = 0
        return path

    def _isAuthorized(self, user, scope, provider, providers):
        values = self._getScopeValues(scope)
        authorized = len(values) > 0
        scopes = ()
        if providers.hasByName(provider):
            users = providers.getByName(provider).getByName('Users')
            if users.hasByName(user):
                scopes = users.getByName(user).getByName('Scopes')
        for value in values:
            if value not in scopes:
                authorized = False
                break
        return authorized

    def getInitData(self):
        return self._user, self._url, self.UrlList

    def getProviderData(self, name):
        providers = self._config.getByName('Providers')
        if providers.hasByName(name):
            data = self._getProviderData(providers.getByName(name))
        else:
            data = self._getDefaultProviderData()
        return self.getProviderTitle(name), data

    def saveProviderData(self, name, clientid, clientsecret, authorizationurl, tokenurl,
                         authorizationparameters, tokenparameters, challenge, challengemethod,
                         signin, page, handler, address, port):
        providers = self._config.getByName('Providers')
        if not providers.hasByName(name):
            providers.insertByName(name, providers.createInstance())
        provider = providers.getByName(name)
        provider.replaceByName('ClientId', clientid)
        provider.replaceByName('ClientSecret', clientsecret)
        provider.replaceByName('AuthorizationUrl', authorizationurl)
        provider.replaceByName('TokenUrl', tokenurl)
        provider.replaceByName('AuthorizationParameters', authorizationparameters)
        provider.replaceByName('TokenParameters', tokenparameters)
        provider.replaceByName('CodeChallenge', challenge)
        provider.replaceByName('CodeChallengeMethod', challengemethod)
        provider.replaceByName('SignIn', signin)
        provider.replaceByName('SignInPage', page)
        provider.replaceByName('HttpHandler', handler)
        provider.replaceByName('RedirectAddress', address)
        provider.replaceByName('RedirectPort', port)
        self.commit()

    def getScopeData(self, name):
        title = self.getScopeTitle(name)
        scopes = self._config.getByName('Scopes')
        if scopes.hasByName(name):
            values = scopes.getByName(name).getByName('Values')
        else:
            values = ()
        return title, values

    def saveScopeData(self, name, provider, values):
        scopes = self._config.getByName('Scopes')
        if not scopes.hasByName(name):
            scopes.insertByName(name, scopes.createInstance())
        scope = scopes.getByName(name)
        scope.replaceByName('Provider', provider)
        # scope.replaceByName('Values', values)
        arguments = ('Values', uno.Any('[]string', tuple(values)))
        uno.invoke(scope, 'replaceByName', arguments)
        self.commit()

    def getMessageBoxData(self):
        return self.getDialogMessage(), self.getDialogTitle()

    def _getProviderData(self, provider):
        clientid = provider.getByName('ClientId')
        clientsecret = provider.getByName('ClientSecret')
        authorizationurl = provider.getByName('AuthorizationUrl')
        tokenurl = provider.getByName('TokenUrl')
        authorizationparameters = provider.getByName('AuthorizationParameters')
        tokenparameters = provider.getByName('TokenParameters')
        codechallenge = provider.getByName('CodeChallenge')
        codechallengemethod = provider.getByName('CodeChallengeMethod')
        signin = provider.getByName('SignIn')
        page = provider.getByName('SignInPage')
        httphandler = provider.getByName('HttpHandler')
        redirectaddress = provider.getByName('RedirectAddress')
        redirectport = provider.getByName('RedirectPort')
        return (clientid, clientsecret, authorizationurl, tokenurl, authorizationparameters, tokenparameters,
                codechallenge, codechallengemethod, signin, page, httphandler, redirectaddress, redirectport)

    def _getDefaultProviderData(self):
        clientid = ''
        clientsecret = ''
        authorizationurl = ''
        tokenurl = ''
        authorizationparameters = '{"prompt": "consent", "response_mode": "query", "scope": null, "login_hint": "current_user", "hl": "current_language"}'
        tokenparameters = '{"scope": null}'
        codechallenge = True
        codechallengemethod = 'S256'
        signin = False
        page = ''
        httphandler = True
        redirectaddress = 'localhost'
        redirectport = 8080
        return (clientid, clientsecret, authorizationurl, tokenurl, authorizationparameters, tokenparameters,
                codechallenge, codechallengemethod, signin, page, httphandler, redirectaddress, redirectport)

    def getUrlData(self, url):
        scope = self._getScope(url)
        provider = self._getProvider(scope)
        return self._getProviderList(), provider, scope

    def addUrl(self, name, scope):
        urls = self._config.getByName('Urls')
        if not urls.hasByName(name):
            urls.insertByName(name, urls.createInstance())
        url = urls.getByName(name)
        url.replaceByName('Scope', scope)
        self.commit()

    def saveUrl(self, url, scope):
        urls = self._config.getByName('Urls')
        if urls.hasByName(url):
             urls.getByName(url).replaceByName('Scope', scope)
             self.commit()

    def removeUrl(self, url):
        urls = self._config.getByName('Urls')
        if urls.hasByName(url):
            urls.removeByName(url)
            self.commit()

    def canRemoveProvider(self, provider):
        scopes = self._config.getByName('Scopes')
        for scope in scopes.ElementNames:
            if scopes.getByName(scope).getByName('Provider') == provider:
                return False
        return True

    def canRemoveScope(self, scope):
        urls = self._config.getByName('Urls')
        for url in urls.ElementNames:
            if urls.getByName(url).getByName('Scope') == scope:
                return False
        return True

    def removeProvider(self, provider):
        providers = self._config.getByName('Providers')
        if providers.hasByName(provider):
            providers.removeByName(provider)
            self.commit()

    def removeScope(self, scope):
        scopes = self._config.getByName('Scopes')
        if scopes.hasByName(scope):
            scopes.removeByName(scope)
            self.commit()

    def isScopeChanged(self, url, scope):
        urls = self._config.getByName('Urls')
        if urls.hasByName(url):
            return urls.getByName(url).getByName('Scope') != scope
        return False

    def getScopeList(self, provider):
        items = []
        scopes = self._config.getByName('Scopes')
        for name in scopes.ElementNames:
            if scopes.getByName(name).getByName('Provider') == provider:
                items.append(name)
        return tuple(items)

    def isConfigurationValid(self, email, url, provider, scope):
        return self.isEmailValid(email) and url != '' and provider != '' and scope != ''

    def isValueValid(self, value):
        return value != ''

    def isEmailValid(self, email):
        if validators.email(email):
            return True
        return False

    def isTextValid(self, text):
        if validators.length(text, 1):
            return True
        return False

    def isUrlValid(self, url):
        if validators.url(url):
            return True
        return False

    def isJsonValid(self, parameters):
        try:
            json.loads(parameters)
        except ValueError as e:
            return False
        return True

    def isDialogValid(self, clientid, authorizationurl, tokenurl, authorizationparameters, tokenparameters, signin, page):
        return (self.isTextValid(clientid) and self.isUrlValid(authorizationurl) and self.isUrlValid(tokenurl)
                and self.isJsonValid(authorizationparameters) and self.isJsonValid(tokenparameters) and (not signin or self.isTextValid(page)))

    def _getScope(self, url):
        scope = ''
        urls = self._config.getByName('Urls')
        if urls.hasByName(url):
            scope = urls.getByName(url).getByName('Scope')
        return scope

    def _getProvider(self, scope):
        provider = ''
        scopes = self._config.getByName('Scopes')
        if scopes.hasByName(scope):
            provider = scopes.getByName(scope).getByName('Provider')
        return provider

    def _getScopeValues(self, scope):
        values = ()
        scopes = self._config.getByName('Scopes')
        if scopes.hasByName(scope):
            values = scopes.getByName(scope).getByName('Values')
        return values

    def _getProviderList(self):
        return self._config.getByName('Providers').ElementNames

# OAuth2Model getter methods called by WizardPages 2
    def getTermsOfUse(self):
        return self._getBaseUrl() % 'TermsOfUse'

    def getPrivacyPolicy(self):
        return self._getBaseUrl() % 'PrivacyPolicy'

    def getAuthorizationStr(self):
        scope = self._config.getByName('Scopes').getByName(self._scope)
        provider = self._config.getByName('Providers').getByName(self._provider)
        scopes = self._getUrlScopes(scope, provider)
        main = provider.getByName('AuthorizationUrl')
        parameters = self._getUrlParameters(scopes, provider)
        arguments = self._getUrlArguments(parameters)
        url = '%s?%s' % (main, arguments)
        if provider.getByName('SignIn'):
            main = self._getSignInUrl(provider)
            parameters = self._getSignInParameters(url)
            arguments = self._getUrlArguments(parameters)
            url = '%s?%s' % (main, arguments)
        return url

    def _getUrlArguments(self, parameters):
        arguments = []
        for key, value in parameters.items():
            arguments.append('%s=%s' % (key, value))
        return '&'.join(arguments)

    def _getSignInUrl(self, provider):
        page = provider.getByName('SignInPage')
        return self._getBaseUrl() % page

    def _getSignInParameters(self, url):
        parameters = {}
        parameters['user'] = self._user
        parameters['url'] = url
        return parameters

    def _getUrlScopes(self, scope, provider):
        scopes = self._getUserScopes(provider)
        for s in scope.getByName('Values'):
            if s not in scopes:
                scopes.append(s)
        return scopes

    def _getUserScopes(self, provider):
        scopes = []
        users = provider.getByName('Users')
        if users.hasByName(self._user):
            scopes = list(users.getByName(self._user).getByName('Scopes'))
        return scopes

# OAuth2Model getter methods called by WizardPages 3
    def getAuthorizationData(self):
        scope = self._config.getByName('Scopes').getByName(self._scope)
        provider = self._config.getByName('Providers').getByName(self._provider)
        scopes = self._getUrlScopes(scope, provider)
        main = provider.getByName('AuthorizationUrl')
        parameters = self._getUrlParameters(scopes, provider)
        url = '%s?%s' % (main, urlencode(parameters))
        if provider.getByName('SignIn'):
            main = self._getSignInUrl(provider)
            parameters = self._getSignInParameters(url)
            url = '%s?%s' % (main, urlencode(parameters))
        msg = "Make HTTP Request: %s?%s" % (main, self._getUrlArguments(parameters))
        self._logger.logp(INFO, 'OAuth2Model', 'getAuthorizationData()', msg)
        return scopes, url

    def startServer(self, scopes, notify, register):
        self._cancelServer()
        provider = self._config.getByName('Providers').getByName(self._provider)
        address = provider.getByName('RedirectAddress')
        port = provider.getByName('RedirectPort')
        lock = Condition()
        server = Server(self._ctx, self._user, self._getBaseUrl(), self._provider, address, port, self._uuid, lock)
        self._watchdog = WatchDog(self._ctx, server, notify, register, scopes, self._provider, self._user, self.HandlerTimeout, lock)
        server.start()
        self._watchdog.start()
        self._logger.logp(INFO, 'OAuth2Manager', 'startServer()', "WizardServer Started ... Done")

    def isServerRunning(self):
        return self._watchdog is not None and self._watchdog.isRunning()

    def registerToken(self, scopes, name, user, code):
        return self._registerToken(scopes, name, user, code)

    def getAuthorizationMessage(self, error):
        return self.getAuthorizationErrorTitle(), self.getRequestErrorMessage(error)

# OAuth2Model getter methods called by WizardPages 4
    def isCodeValid(self, code):
        return code != ''

    def setAuthorization(self, code):
        scope = self._config.getByName('Scopes').getByName(self._scope)
        provider = self._config.getByName('Providers').getByName(self._provider)
        scopes = self._getUrlScopes(scope, provider)
        return self._registerToken(scopes, self._provider, self._user, code)

# OAuth2Model getter methods called by WizardPages 5
    def closeWizard(self):
        return self._close

    def getTokenData(self):
        label = self.getTokenLabel()
        never, scopes, access, refresh, expires = self.getUserTokenData()
        return label, never, scopes, access, refresh, expires

    def getUserTokenData(self):
        users = self._config.getByName('Providers').getByName(self._provider).getByName('Users')
        user = users.getByName(self._user)
        scopes = user.getByName('Scopes')
        refresh = user.getByName('RefreshToken') if user.hasByName('RefreshToken') else self.getTokenRefresh()
        access = user.getByName('AccessToken') if user.hasByName('AccessToken') else self.getTokenAccess()
        timestamp = user.getByName('TimeStamp')
        never = user.getByName('NeverExpires')
        expires = self.getTokenExpires() if never else timestamp - int(time.time())
        return never, scopes, access, refresh, expires

    def refreshToken(self):
        provider = self._config.getByName('Providers').getByName(self._provider)
        user = provider.getByName('Users').getByName(self._user)
        return self._refreshToken(provider, user, True)

    def _refreshToken(self, provider, user, multiline):
        url = provider.getByName('TokenUrl')
        data = self._getRefreshParameters(user, provider)
        timestamp = int(time.time())
        response, error = self._getResponseFromRequest(url, data, multiline)
        if error is None:
            refresh, access, never, expires = self._getTokenFromResponse(response, timestamp)
            self._saveRefreshedToken(user, refresh, access, never, expires)
        return error

    def deleteUser(self):
        providers = self._config.getByName('Providers')
        if providers.hasByName(self._provider):
            provider = providers.getByName(self._provider)
            users = provider.getByName('Users')
            if users.hasByName(self._user):
                users.removeByName(self._user)
                self.commit()

    def _getRefreshParameters(self, user, provider):
        parameters = self._getRefreshBaseParameters(user, provider)
        optional = self._getRefreshOptionalParameters(user, provider)
        option = provider.getByName('TokenParameters')
        parameters = self._parseParameters(parameters, optional, option)
        return parameters
    
    def _getRefreshBaseParameters(self, user, provider):
        parameters = {}
        parameters['refresh_token'] = user.getByName('RefreshToken')
        parameters['grant_type'] = 'refresh_token'
        parameters['client_id'] = provider.getByName('ClientId')
        return parameters
    
    def _getRefreshOptionalParameters(self, user, provider):
        parameters = {}
        parameters['scope'] = ' '.join(user.getByName('Scopes'))
        parameters['client_secret'] = provider.getByName('ClientSecret')
        return parameters

 # OAuth2Model private getter methods called by WizardPages 1 and WizardPages 3
    def _getBaseUrl(self):
        return self._config.getByName('BaseUrl')

# OAuth2Model private getter methods called by WizardPages 2 and WizardPages 3
    def _getCodeVerifier(self):
        return self._uuid + self._uuid

    def _getRedirectUri(self, provider):
        if provider.getByName('HttpHandler'):
            uri = self._uri % (provider.getByName('RedirectAddress'), provider.getByName('RedirectPort'))
        else:
            uri = self._urn
        return uri

    def _getUrlParameters(self, scopes, provider):
        parameters = self._getUrlBaseParameters(provider)
        optional = self._getUrlOptionalParameters(scopes, provider)
        option = provider.getByName('AuthorizationParameters')
        parameters = self._parseParameters(parameters, optional, option)
        return parameters

    def _getUrlBaseParameters(self, provider):
        parameters = {}
        parameters['response_type'] = 'code'
        parameters['client_id'] = provider.getByName('ClientId')
        parameters['state'] = self._uuid
        parameters['redirect_uri'] = self._getRedirectUri(provider)
        if provider.getByName('CodeChallenge'):
            method = provider.getByName('CodeChallengeMethod')
            parameters['code_challenge_method'] = method
            parameters['code_challenge'] = self._getCodeChallenge(method)
        return parameters

    def _getUrlOptionalParameters(self, scopes, provider):
        parameters = {}
        parameters['scope'] = ' '.join(scopes)
        parameters['client_secret'] = provider.getByName('ClientSecret')
        parameters['current_user'] = self._user
        parameters['current_language'] = getCurrentLocale(self._ctx).Language
        return parameters

    def _getCodeChallenge(self, method):
        print("OAuth2Model._getCodeChallenge() 1")
        code = self._getCodeVerifier()
        if method == 'S256':
            if isinstance(code, string_types):
                print("OAuth2Model._getCodeChallenge() 2")
                code = code.encode('utf-8')
            code = hashlib.sha256(code).digest()
            padding = {0:0, 1:2, 2:1}[len(code) % 3]
            challenge = base64.urlsafe_b64encode(code).decode('utf-8')
            code = challenge[:len(challenge)-padding]
        return code

# OAuth2Model private getter/setter methods called by WizardPages 3 and WizardPages 4
    def _registerToken(self, scopes, name, user, code):
        provider = self._config.getByName('Providers').getByName(name)
        url = provider.getByName('TokenUrl')
        parameters = self._getTokenParameters(scopes, provider, code)
        msg = "Make HTTP Request: %s?%s" % (url, self._getUrlArguments(parameters))
        self._logger.logp(INFO, 'OAuth2Model', '_registerToken()', msg)
        timestamp = int(time.time())
        response, error = self._getResponseFromRequest(url, parameters)
        if error is None:
            self._saveUserToken(scopes, provider, user, response, timestamp)
        msg = "Receive Response: %s" % (response, )
        self._logger.logp(INFO, 'OAuth2Model', '_registerToken()', msg)
        return error

    def _getTokenParameters(self, scopes, provider, code):
        parameters = self._getTokenBaseParameters(provider, code)
        optional = self._getTokenOptionalParameters(scopes, provider)
        option = provider.getByName('TokenParameters')
        parameters = self._parseParameters(parameters, optional, option)
        return parameters

    def _getTokenBaseParameters(self, provider, code):
        parameters = {}
        parameters['code'] = code
        parameters['grant_type'] = 'authorization_code'
        parameters['client_id'] = provider.getByName('ClientId')
        parameters['redirect_uri'] = self._getRedirectUri(provider)
        if provider.getByName('CodeChallenge'):
            parameters['code_verifier'] = self._getCodeVerifier()
        return parameters

    def _getTokenOptionalParameters(self, scopes, provider):
        parameters = {}
        parameters['scope'] = ' '.join(scopes)
        parameters['client_secret'] = provider.getByName('ClientSecret')
        return parameters

    def _saveUserToken(self, scopes, provider, name, response, timestamp):
        users = provider.getByName('Users')
        if not users.hasByName(name):
            users.insertByName(name, users.createInstance())
        user = users.getByName(name)
        # user.replaceByName('Scopes', scopes)
        arguments = ('Scopes', uno.Any('[]string', tuple(scopes)))
        uno.invoke(user, 'replaceByName', arguments)
        refresh, access, never, expires = self._getTokenFromResponse(response, timestamp)
        self._saveTokens(user, refresh, access, never, expires)

# OAuth2Model private getter/setter methods
    def _parseParameters(self, base, optional, required):
        for key, value in json.loads(required).items():
            if value is None:
                if key in base:
                    del base[key]
                elif key in optional:
                    base[key] = optional[key]
            elif value in optional:
                base[key] = optional[value]
            else:
                base[key] = value
        return base

    def _getResponseFromRequest(self, url, data, multiline=True):
        response = {}
        error = None
        session = Session()
        with session as s:
            try:
                print("OAuth2Model._getResponseFromRequest() Url: %s - Data: %s - Timeout: %s" % (url, data, self.Timeout))
                with s.post(url, data=data, timeout=self.Timeout, verify=False) as r:
                    response = r.json()
                    r.raise_for_status()
            except ConnectionError:
                # TODO: The provided url may be unreachable
                error = self.getRequestErrorMessage(300) %  (url, repr(traceback.format_exc()))
                self._logger.logp(SEVERE, 'OAuth2Model', '_getResponseFromRequest()', error)
            except json.decoder.JSONDecodeError:
                # TODO: Normally the content of the page must be in json format,
                # TODO: except if we are not on the right page for example.
                ctype = r.headers.get('Content-Type', 'undefined')
                error = self.getRequestErrorMessage(301) % (ctype, r.status_code, url)
                self._logger.logp(SEVERE, 'OAuth2Model', '_getResponseFromRequest()', error)
                if multiline and r.text != '':
                    error += self.getRequestErrorMessage(302) % r.text
            except HTTPError:
                # TODO: Catch OAuth2 'error' and 'error_description' to display them to facilitate debugging.
                error = self.getRequestErrorMessage(getOAuth2ErrorCode(response.get('error')))
                self._logger.logp(SEVERE, 'OAuth2Model', '_getResponseFromRequest()', error)
                description = response.get('error_description')
                if multiline:
                    if description is not None:
                        error += self.getRequestErrorMessage(303) % description
                    elif r.text != '':
                        error += self.getRequestErrorMessage(302) % r.text
        return response, error

    def _getTokenFromResponse(self, response, timestamp):
        refresh = response.get('refresh_token', None)
        access = response.get('access_token', None)
        expires = response.get('expires_in', None)
        never = expires is None
        return refresh, access, never, 0 if never else timestamp + expires

    def _saveTokens(self, user, refresh, access, never, timestamp):
        if refresh is not None:
            user.replaceByName('RefreshToken', refresh)
        self._saveRefreshedToken(user, refresh, access, never, timestamp)

    def _saveRefreshedToken(self, user, refresh, access, never, timestamp):
        if access is not None:
            user.replaceByName('AccessToken', access)
        user.replaceByName('NeverExpires', never)
        user.replaceByName('TimeStamp', timestamp)
        self.commit()

# OAuth2Model StringResource methods
    def getPageStep(self, pageid):
        resource = self._resources.get('Step') % pageid
        return self._resolver.resolveString(resource)

    def getPageTitle(self, pageid):
        resource = self._resources.get('Title') % pageid
        return self._resolver.resolveString(resource)

    def getUrlLabel(self, url):
        resource = self._resources.get('UrlLabel')
        return self._resolver.resolveString(resource) % url

    def getProviderTitle(self, name):
        resource = self._resources.get('ProviderTitle')
        return self._resolver.resolveString(resource) % name

    def getScopeTitle(self, name):
        resource = self._resources.get('ScopeTitle')
        return self._resolver.resolveString(resource) % name

    def getTokenLabel(self):
        resource = self._resources.get('TokenLabel')
        return self._resolver.resolveString(resource) % (self._provider, self._user)

    def getTokenAccess(self):
        resource = self._resources.get('TokenAccess')
        return self._resolver.resolveString(resource)

    def getTokenRefresh(self):
        resource = self._resources.get('TokenRefresh')
        return self._resolver.resolveString(resource)

    def getTokenExpires(self):
        resource = self._resources.get('TokenExpires')
        return self._resolver.resolveString(resource)

    def getDialogTitle(self):
        resource = self._resources.get('DialogTitle')
        return self._resolver.resolveString(resource)

    def getDialogMessage(self):
        resource = self._resources.get('DialogMessage')
        return self._resolver.resolveString(resource)

    def getUserTitle(self, provider):
        resource = self._resources.get('UserTitle')
        return self._resolver.resolveString(resource) % provider

    def getUserLabel(self, msg):
        resource = self._resources.get('UserLabel')
        return self._resolver.resolveString(resource) % msg

    def getAuthorizationErrorTitle(self):
        resource = self._resources.get('AuthorizationError')
        return self._resolver.resolveString(resource)

    def getTokenErrorTitle(self):
        resource = self._resources.get('TokenError')
        return self._resolver.resolveString(resource)

    def getRequestErrorMessage(self, error):
        resource = self._resources.get('RequestMessage')
        return self._resolver.resolveString(resource % error)

