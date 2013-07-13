:mod:`synctools` --- utilities for syncing simfiles
===================================================

This module provides several commands that assist syncing simfiles for StepMania and In The Groove. The commands can be accessed through both command-line and graphical interfaces.

Members
-------

.. automodule:: synctools.command
    :members: SynctoolsCommand, FieldInputs, FieldTypes

.. automodule:: synctools.utils
    :members: get_commands, find_simfiles

Example usage
-------------

The source for :class:`AdjustOffset` serves as a good example of a basic command:

.. literalinclude:: ../../synctools/commands/adjustoffset.py

There are a few important things to note here:

* Always remember to put ``super(ClassName, self).run(simfile)`` at the beginning of the :meth:`run` method, and likewise for :meth:`__init__` and :meth:`done` if they are being overridden as well.
* Any command that modifies and saves the input simfiles should include ``command.common_fields['backup']`` in its `fields` attribute. Bear in mind that backups are made automatically by the ``super(...).run(...)`` line described above.
* Don't check the types / values of the option fields from within the :meth:`run` method. In the above code, ``self.options['amount']`` is guaranteed to be valid because the field's type is set to :py:class:`Decimal`, which rejects invalid input. Fields that require unusual constraints should have a function defined above the class definition that validates the input, and the field's type should be set to that function.
* Although their use is not demonstrated in the above code, remember to use the attributes of :class:`FieldTypes` where applicable.