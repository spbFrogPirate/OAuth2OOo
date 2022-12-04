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

from ....unotool import getDialog
from ....logger import logMessage
from ....configuration import g_extension

import traceback

class ProviderView(unohelper.Base):
    def __init__(self, ctx, handler, parent, title):
        self._dialog = getDialog(ctx, g_extension, 'ProviderDialog', handler, parent)
        self._dialog.setTitle(title)

# ProviderView getter methods
    def execute(self):
        return self._dialog.execute()

    def getDialogValues(self):
        return (self.getClientId(), self.getAuthorizationUrl(), self.getTokenUrl(),
                self.getAuthorizationParameters(), self.getTokenParameters())

    def getDialogData(self):
        clientid, authorizationurl, tokenurl, authorizationparameters, tokenparameters = self.getDialogValues()
        data = (self.getRedirectAddress(), self.getRedirectPort(), self.getClientSecret(),
                self.getCodeChallenge(), self.getCodeChallengeMethod(), clientid,
                authorizationurl, tokenurl, authorizationparameters, tokenparameters)
        return self.getHttpHandler(), data

    def getClientId(self):
        return self._getClientId().Text.strip()

    def getAuthorizationUrl(self):
        return self._getAuthorizationUrl().Text.strip()

    def getTokenUrl(self):
        return self._getTokenUrl().Text.strip()

    def getCodeChallenge(self):
        return bool(self._getCodeChallenge().State)

    def getCodeChallengeMethod(self):
        return 'S256' if self._getCodeChallengeMethod(1).State else 'plain'

    def getClientSecret(self):
        return self._getClientSecret().Text.strip()

    def getAuthorizationParameters(self):
        return self._getAuthorizationParameters().Text.strip()

    def getTokenParameters(self):
        return self._getTokenParameters().Text.strip()

    def getRedirectAddress(self):
        return self._getRedirectAddress().getSelectedItem()

    def getRedirectPort(self):
        return int(self._getRedirectPort().Value)

    def getHttpHandler(self):
        return bool(self._getHttpHandler(3).State)

# ProviderView setter methods
    def initDialog(self, clientid, authorizationurl, tokenurl, codechallenge, codechallengemethod,
                   clientsecret, authorizationparameters, tokenparameters,
                   redirectaddress, redirectport, httphandler):
        self._getClientId().Text = clientid
        self._getAuthorizationUrl().Text = authorizationurl
        self._getTokenUrl().Text = tokenurl
        self._getCodeChallenge().State = 1 if codechallenge else 0
        option = 1 if codechallengemethod == 'S256' else 2
        self._getCodeChallengeMethod(option).State = 1
        self.enableChallengeMethod(codechallenge)
        self._getClientSecret().Text = clientsecret
        self._getAuthorizationParameters().Text = authorizationparameters
        self._getTokenParameters().Text = tokenparameters
        self._getRedirectAddress().selectItem(redirectaddress, True)
        self._getRedirectPort().Value = '%s' % redirectport
        option = 3 if httphandler else 4
        self._getHttpHandler(option).State = 1
        self.enableHttpHandler(httphandler)

    def dispose(self):
        self._dialog.dispose()

    def enableChallengeMethod(self, enabled):
        self._getCodeChallengeMethod(1).Model.Enabled = enabled
        self._getCodeChallengeMethod(2).Model.Enabled = enabled

    def enableHttpHandler(self, enabled):
        self._getRedirectAddressLabel().Model.Enabled = enabled
        self._getRedirectAddress().Model.Enabled = enabled
        self._getRedirectPortLabel().Model.Enabled = enabled
        self._getRedirectPort().Model.Enabled = enabled

    def updateOk(self, enabled):
        self._getOkButton().Model.Enabled = enabled

    def setClientId(self, clientid):
        self._getClientId().Text = clientid

    def setAuthorizationUrl(self, url):
        self._getAuthorizationUrl().Text = url

    def setTokenUrl(self, url):
        self._getTokenUrl().Text = url

    def setCodeChallenge(self, state):
        self._getCodeChallenge().State = state

    def setCodeChallengeMethod(self, method):
        option = 1 if method == 'S256' else 2
        self._getCodeChallengeMethod(option).State = 1

    def setClientSecret(self, secret):
        self._getClientSecret().Text = secret

    def setAuthorizationParameters(self, parameters):
        self._getAuthorizationParameters().Text = parameters

    def setTokenParameters(self, parameters):
        self._getTokenParameters().Text = parameters

    def setRedirectAddress(self, address):
        self._getRedirectAddress().selectItem(address, True)

    def setRedirectPort(self, port):
        self._getRedirectPort().Value = port

    def setHttpHandler(self, enabled):
        position = 3 if enabled else 4
        self._getHttpHandler(position).State = 1

# ProviderView private getter control methods
    def _getClientId(self):
        return self._dialog.getControl('TextField1')

    def _getAuthorizationUrl(self):
        return self._dialog.getControl('TextField2')

    def _getTokenUrl(self):
        return self._dialog.getControl('TextField3')

    def _getClientSecret(self):
        return self._dialog.getControl('TextField4')

    def _getAuthorizationParameters(self):
        return self._dialog.getControl('TextField5')

    def _getTokenParameters(self):
        return self._dialog.getControl('TextField6')

    def _getCodeChallengeMethod(self, option):
        return self._dialog.getControl('OptionButton%s' % option)

    def _getCodeChallenge(self):
        return self._dialog.getControl('CheckBox1')

    def _getRedirectAddress(self):
        return self._dialog.getControl('ListBox1')

    def _getRedirectPort(self):
        return self._dialog.getControl('NumericField1')

    def _getHttpHandler(self, option):
        return self._dialog.getControl('OptionButton%s' % option)

    def _getRedirectAddressLabel(self):
        return self._dialog.getControl('Label9')

    def _getRedirectPortLabel(self):
        return self._dialog.getControl('Label10')

    def _getOkButton(self):
        return self._dialog.getControl('CommandButton2')

