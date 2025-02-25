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

from .options import OptionsManager

from .configuration import g_extension
from .configuration import g_identifier
from .configuration import g_oauth2
from .configuration import g_defaultlog
from .configuration import g_errorlog
from .configuration import g_basename

from .unotool import createService
from .unotool import getDialog
from .unotool import getParentWindow
from .unotool import getStringResource
from .unotool import getSimpleFile

from .dialog import UserHandler
from .dialog import UserView

from .logger import getLogger

from .oauth2model import OAuth2Model

from .request import download
from .request import getInputStream
from .request import getSessionMode
from .request import upload

from .requestresponse import getRequestResponse

from .requestparameter import RequestParameter

from .oauth2 import OAuth2OOo
from .oauth2 import NoOAuth2
from .oauth2 import InteractionRequest
from .oauth2 import getOAuth2UserName

from .oauth2helper import getAccessToken
from .oauth2helper import showOAuth2Wizard

