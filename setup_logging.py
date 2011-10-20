"""
    When using pytality, and the graphical console in general,
    using "print" will be disasterous. All output should go through the logging module.

    To make things even more confusing, when using Silverlight, the filesystem is
    read-only - so just writing to a logfile doesn't work either!


    This module will setup logging in a way that will work on all platforms, as soon
    as the pytality package is imported. If you don't want this, configure the logging
    module before importing Pytality and it will use your configuration instead.

    You can set two properties on the "logging" module to modify the automatic configuration:

    logging.fileName:
        The filename to use for the logfile when one is used.
        Defaults to "debug.log".

    logging.baseFormat:
        The message format to use.
        defaults to "%(asctime)s %(name)s:%(levelname)s %(message)s"

    logging.logLevel:
        The default loglevel to use.
        Defaults to logging.DEBUG.
    
    logging.clearOnInit:
        Set to true to clear the logfile during setup, when one is used.
        Defaults to True.

    logging.allowPrint:
        Set to true to leave sys.stdout / "print" alone.
        Defaults to False. Always false on silverlight.

"""
import sys

import logging
if len(logging.root.handlers) == 0:
    #get the user variables, if any
    filename = getattr(logging, 'fileName', 'debug.log')
    base_format = getattr(logging, 'baseFormat', "%(asctime)s %(name)s:%(levelname)s %(message)s")
    log_level = getattr(logging, 'logLevel', logging.DEBUG)
    clear_on_init = getattr(logging, 'clearOnInit', True)
    allow_print = getattr(logging, 'allowPrint', False)

    #setup handlers based on platform
    if sys.platform == 'silverlight':
        #silverlight
        #stdout actually IS our log destination
        hdlr = logging.StreamHandler(sys.stdout)

    else:
        #not silverlight
        #use logfiles.

        if clear_on_init:
            with open(filename, 'w') as logfile:
                logfile.write('')

        hdlr = logging.FileHandler(filename)

        #hook stdout/print if desired
        if not allow_print:
            print_logger = logging.getLogger("print")
            class StdoutWrapper(object):
                def write(self, s):
                    print_logger.debug(s)

    #setup formatters
    formatter = logging.Formatter(base_format)
    
    #attach it together
    logger = logging.getLogger('')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(log_level)

    logging.getLogger("pytality").debug("Logging set up successfully")
