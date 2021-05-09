from __future__ import print_function, unicode_literals
from __future__ import with_statement
import textwrap
from contextlib import contextmanager
try:
    from StringIO import StringIO ## for Python 2
except ImportError:
    from io import StringIO ## for Python 3
from PyInquirer import style_from_dict, Token, prompt, Separator
from pprint import pprint
from pyfiglet import Figlet

INDENT = ' ' * 4

class IndentManager(object):
    """
    A context manager for indentation. Used internally by the source manager
    to provide the indent context manager. And the indent and dedent methods.
    """
    def __init__(self, indent_with=INDENT):
        self.indent_with = indent_with
        self.level = 0

    def __call__(self):
        """
        Raise the indentation level if this instance is called like a method.
        """
        self.indent()

    def __str__(self):
        """
        self.indent_with multiplied by the current indentation level.
        Used to indent strings to the correct depth.
        """
        return self.indent_with * self.level

    def __enter__(self):
        """
        Start of an indentation context.
        """
        self.indent()
        return self

    def __exit__(self, *exc_info):
        """
        Ends of an indentation context, so dedent.
        """
        self.dedent()

    def indent(self):
        """Raise the indentation level by 1."""
        self.level = self.level + 1
        return self

    def dedent(self):
        """
        Decrease the indentation level by one. If the indentation level is
        already at zero a ``DedentException`` is raised.
        """
        if self.level == 0:
            raise DedentException('Indent level is already at zero.')
        self.level = self.level - 1

    def reset(self):
        """
        Reset the indentation level to zero.
        """
        self.level = 0


class SourceBuilder(object):
    """
    A basic source code writer.
    Usage
    -----
    Create a SourceBuilder instance  and write code to it to line by line.
    By using the ``indent`` context manager each line gets correctly indented
    and the input indentation will resemble the output::
      >>> sb = SourceBuilder()
      >>> sb.writeln()
      >>> sb.writeln('def hello_world():')
      >>> with sb.indent:
      ...     sb.writeln('print \'Hello World\'')
      ...
      ...
      >>> sb.writeln()
      >>> sb.writeln('hello_world()')
      >>> source = sb.end()
      >>> print source
      def hello_world():
          print 'Hello World'
      hello_world()
    If for some reason context managers can't be used ``indent`` also works
    as a method. Combined with the ``dedent`` method code indentation levels
    can be controlled manually.::
      >>> sb = SourceBuilder()
      >>> sb.writeln()
      >>> sb.writeln('def hello_world():')
      >>> sb.indent()
      >>> sb.writeln('print \'Hello World\'')
      >>> sb.dedent()
      >>> sb.writeln()
      >>> sb.writeln('hello_world()')
      >>> source = sb.end()
      >>> print source
      def hello_world():
           print 'Hello World'
      hello_world()
    It's not advised to use ``sb.indent`` in ``with`` statements in combination
    with calls to ``sb.dedent()`` or ``sb.indent()``.
    """
    def __init__(self, indent_with=INDENT):
        """
        Initialize SourceBuilder, ``indent_with`` is set to 4 spaces
        by default.
        """
        self._out = StringIO()
        self.indent = IndentManager(indent_with=indent_with)

    def write(self, code):
        """
        Write code at the current indentation level.
        """
        self._out.write(str(self.indent))
        self._out.write(code)

    def writeln(self, code=''):
        """
        Write a line at the current indentation level.
        If no code is given only a newline is written.
        """
        if code:
            self.write(code)
        self._out.write('\n')

    def dedent(self):
        """
        Decrease the current indentation level. Should only be used if
        the indent context manager is not used.
        Raises a ``DedentException`` if decreasing indentation level is not
        possible.
        """
        self.indent.dedent()

    def end(self):
        """
        Get the generated source and resets the indent level.
        """
        self.indent.reset()
        return self._out.getvalue()

    def truncate(self):
        '''
        Discard generated source and memory buffer and resets the indent level.
        '''
        if not self._out.closed:
            self._out.close()
        self._out = StringIO()
        self.indent.reset()

    def close(self):
        '''
        Convenience method for use with ``contextlib.closing``.
        Calls ``self.truncate()``.
        '''
        self.truncate()


INDENT = ' ' * 4
TRIPLE_QUOTES = '"' * 3
DOCSTRING_WIDTH = 72


class PySourceBuilder(SourceBuilder):
    """
    A special SourceBuilder that provides some convenience context managers
    for writing well formatted Python code.
    """
    def __init__(self, indent_with=INDENT):
        super(PySourceBuilder, self).__init__(indent_with=indent_with)

    @contextmanager
    def block(self, code, lines_before=0):
        """
        A context manager for block structures. It's a generic way to start a
        control structure (if, try, while, for etc.) or a class, function or
        method definition.
        The given ``code`` will be printed preceded by 0 or more blank lines,
        controlled by the ``lines_before`` parameter. An indent context is
        then started.
        Example::
            sb = PySourceBuilder()
            >>>
            >>> with sb.block('class Hello(object):', 2):
            ...     with sb.block('def __init__(self, what=\'World\'):', 1):
            ...         sb.writeln('pass')
            ...
            >>> print sb.end()
            class Hello(object):
                def __init__(self, what='World'):
                    pass
        """
        for i in range(lines_before):
            self.writeln()
        self.writeln(code)
        with self.indent:
            yield

    def docstring(self, doc, delimiter=TRIPLE_QUOTES, width=DOCSTRING_WIDTH):
        """
        Write a docstring. The given ``doc`` is surrounded by triple double
        quotes (\"\"\"). This can be changed by passing a different
        ``delimiter`` (e.g. triple single quotes).
        The docstring is formatted to not run past 72 characters per line
        (including indentation). This can be changed by passing a different
        ``width`` parameter.
        """
        doc = textwrap.dedent(doc).strip()
        max_width = width - len(str(self.indent))
        lines = doc.splitlines()
        if len(lines) == 1 and len(doc) < max_width - len(delimiter) * 2:
            self.writeln(u'%s%s%s' % (delimiter, doc, delimiter))
        else:
            self.writeln(delimiter)
            for line in lines:
                if not line.strip():
                    self.writeln()
                for wrap in textwrap.wrap(line, max_width):
                    self.writeln(wrap)
            self.writeln()
            self.writeln(delimiter)


print("\n")
f = Figlet(font='slant')
print(f.renderText('Quantconnect'))
print("\n")

style = style_from_dict({
    Token.Separator: '#cc5454',
    Token.QuestionMark: '#673ab7 bold',
    Token.Selected: '#cc5454',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Instruction: '',  # default
    Token.Answer: '#f44336 bold',
    Token.Question: '',
})

print("Let's build a strategy!")

questions = [
    {
        'type': 'list',
        'message': 'Choose an alpha',
        'name': 'alpha',
        'choices': [
            Separator('\n= Alpha ='),
            {
                'name': 'RSI'
            },
            {
                'name': 'EMA Cross'
            },
            {
                'name': 'MACD'
            },
            {
                'name': 'Historical Returns'
            },
            {
                'name': 'Pairs Trading'
            },
            {
                'name': 'None'
            }
        ],

        'validate': lambda answer: 'You must choose one of these' \
            if len(answer) == 0 else True

    },
    {
        'type': 'list',
        'message': 'Choose an universe',
        'name': 'universe',
        'choices': [
            Separator('\n= Universe ='),
            {
                'name': 'Large Cap Equities'
            },
            {
                'name': 'EMA Cross Universe'
            },
            {
                'name': 'Coarse Universe'
            },
            {
                'name': 'Coarse-Fine Universe'
            },
            {
                'name': 'Scheduled Universe'
            },
            {
                'name': 'Manual Selection'
            },
            {
                'name': 'None'
            }
        ],
        'validate': lambda answer: 'You must choose at least one of these' \
            if len(answer) == 0 else True
    },

    {
        'type': 'list',
        'message': 'Choose the construction of your portfolio',
        'name': 'portfolio',
        'choices': [
            Separator('\n= Portfolio ='),
            {
                'name': 'Equal Weighting'
            },
            {
                'name': 'Mean-Variance'
            },
            {
                'name': 'Black Litterman'
            },
            {
                'name': 'None'
            }
        ],
        'validate': lambda answer: 'You must choose at least one of these' \
            if len(answer) == 0 else True
    },
    {
            'type': 'list',
            'message': 'Choose the type of execution',
            'name': 'execution',
            'choices': [
                Separator('\n= Execution ='),
                {
                    'name': 'Immediate'
                },
                {
                    'name': 'VWAP'
                },
                {
                    'name': 'Standard deviation'
                },
                {
                    'name': 'None'
                }
            ],
            'validate': lambda answer: 'You must choose at least one of these' \
                if len(answer) == 0 else True
        },
            {
                    'type': 'list',
                    'message': 'Choose the type of risk management',
                    'name': 'risk',
                    'choices': [
                        Separator('\n= Risk ='),
                        {
                            'name': 'Maximum Drawdown'
                        },
                        {
                            'name': 'Sector Exposure'
                        },
                        {
                            'name': 'None'
                        }
                    ],
                    'validate': lambda answer: 'You must choose at least one of these' \
                        if len(answer) == 0 else True
                },
            {
                    'type': 'input',
                    'message': 'Type the start date in this format YYYY, MM, DD (e.g : 2017, 1, 1)',
                    'name': 'start',
                    'validate': lambda answer: 'You must choose at least one of these' \
                        if len(answer) == 0 else True
                },
            {
                    'type': 'input',
                    'message': 'Set Strategy cash (e.g : 100000)',
                    'name': 'cash',
                    'validate': lambda answer: 'You must choose at least one of these' \
                        if len(answer) == 0 else True
                },
            {
                    'type': 'confirm',
                    'message': 'Build the strategy? (make sure there is no strategy.py file in this directory)',
                    'name': 'build',
                    'validate': lambda answer: 'You must choose at least one of these' \
                        if len(answer) == 0 else True
                }
]

answers = prompt(questions, style=style)

factors = []
for n in answers:
    list = answers[n]
    factors.append(list)


#code generation
sb = SourceBuilder()
klasses = ['DancingBlueOwl']
for klass in klasses:
     sb.writeln('class {0}(QCAlgorithm):'.format(klass))
     sb.writeln()
     with sb.indent:
         sb.writeln('def Initialize(self):')
         with sb.indent:

             sb.writeln('self.SetStartDate('+factors[5]+') # Set Start Date')
             sb.writeln('self.SetCash('+factors[6]+') # Set Strategy Cash')
             sb.writeln('#self.AddEquity("SPY", Resolution.Minute)')
             sb.writeln()

              #alpha
             if factors[0] == "RSI":
               sb.writeln('self.AddAlpha(RsiAlphaModel(60, Resolution.Minute))')

             if factors[0] == "EMA Cross":
               sb.writeln('self.AddAlpha(EmaCrossAlphaModel(50, 200, Resolution.Minute))')

             if factors[0] == "MACD":
               sb.writeln('self.AddAlpha(MacdAlphaModel(12, 26, 9, MovingAverageType.Simple, Resolution.Daily))')

             if factors[0] == "Historical Returns":
               sb.writeln('self.AddAlpha(HistoricalReturnsAlphaModel(14, Resolution.Daily))')

             if factors[0] == "Pairs Trading":
               sb.writeln('self.AddAlpha(PearsonCorrelationPairsTradingAlphaModel(252, Resolution.Daily))')

             if factors[0] == "None":
               pass

             sb.writeln()

             #execution
             if factors[3] == "Immediate":
               sb.writeln('self.SetExecution(ImmediateExecutionModel())')

             if factors[3] == "VWAP":
               sb.writeln('self.SetExecution(VolumeWeightedAveragePriceExecutionModel())')

             if factors[3] == "Standard deviation":
               sb.writeln('self.SetExecution(StandardDeviationExecutionModel(60, 2, Resolution.Minute))')

             if factors[3] == "None":
                 pass

             sb.writeln()

             #portfolio

             if factors[2] == "Equal Weighting":
               sb.writeln('self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())')

             if factors[2] == "Mean-Variance":
               sb.writeln('self.SetPortfolioConstruction(MeanVarianceOptimizationPortfolioConstructionModel())')

             if factors[2] == "Black Litterman":
               sb.writeln('self.SetPortfolioConstruction(BlackLittermanOptimizationPortfolioConstructionModel())')

             if factors[2] == "None":
                 pass

             sb.writeln()

             #risk management

             if factors[4] == "Maximum Drawdown":
               sb.writeln('self.SetRiskManagement(MaximumDrawdownPercentPerSecurity(0.01))')

             if factors[4] == "Sector Exposure":
               sb.writeln('self.SetRiskManagement(MaximumSectorExposureRiskManagementModel())')

             if factors[4] == "None":
                 pass

             sb.writeln()




             #universe
             if factors[1] == "Large Cap Equities":
               sb.writeln('self.SetUniverseSelection(QC500UniverseSelectionModel())')

             if factors[1] == "EMA Cross Universe":
               sb.writeln('fastPeriod = 10')
               sb.writeln('slowPeriod = 30')
               sb.writeln('count = 10')
               sb.writeln('self.SetUniverseSelection(EmaCrossUniverseSelectionModel(fastPeriod, slowPeriod, count))')

             if factors[1] == "Coarse Universe":
               sb.writeln('self.SetUniverseSelection(CoarseFundamentalUniverseSelectionModel(self.CoarseSelectionFunction))')

             if factors[1] == "Coarse-Fine Universe":
               sb.writeln('self.__numberOfSymbols = 100')
               sb.writeln('self.__numberOfSymbolsFine = 5')
               sb.writeln('self.SetUniverseSelection(FineFundamentalUniverseSelectionModel(self.CoarseSelectionFunction, self.FineSelectionFunction, None, None))')

             if factors[1] == "Scheduled Universe":
               sb.writeln('# selection will run on mon/tues/thurs at 00:00/06:00/12:00/18:00')
               sb.writeln('self.SetUniverseSelection(ScheduledUniverseSelectionModel(')
               with sb.indent:
                          sb.writeln('self.DateRules.Every(DayOfWeek.Monday, DayOfWeek.Tuesday, DayOfWeek.Thursday),')
                          sb.writeln('self.TimeRules.Every(timedelta(hours = 12)),')
                          sb.writeln('self.SelectSymbols')
               sb.writeln('))')

             if factors[1] == "Manual Selection":
               sb.writeln('symbols = [ Symbol.Create("SPY", SecurityType.Equity, Market.USA) ]')
               sb.writeln('self.SetUniverseSelection( ManualUniverseSelectionModel(symbols) )')

             if factors[1] == "None":
                 pass


             sb.writeln()
             sb.writeln()
     with sb.indent:
      sb.writeln('def OnData(self, data):')
      with sb.indent:
             sb.writeln('# if not self.Portfolio.Invested:')
             sb.writeln('#    self.SetHoldings("SPY", 1)')


source = sb.end()

with open('strategy.py', 'a') as file:
    print(source, file=file)
print("Just created the strategy.py file!")
