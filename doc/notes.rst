=====
Notes
=====

.. _core-api-common-params:

khiops.core.api common parameters
=================================
The functions in the `khiops.core.api` have the following common parameters.

log_file_path : str, default ""
    Path of the log file for the Khiops process (command line option ``-e`` of the desktop app). If
    equal to "" then it writes no log file.
output_scenario_path : str, default ""
    Path of the output Khiops scenario file (command line option ``-o`` of the desktop app).  If
    the empty string is specified no output scenario file is generated.
task_file_path : str, default ""
    Path of the task file for the Khiops process (command line option ``-p`` of the desktop app). If
    equal to "" then it writes no task file.
trace : bool, default ``False``
    If True prints the command line executed of the process and does not delete any temporary files
    created.
stdout_file_path : str, default ""
    *Advanced* Path to a file where the Khiops process writes its stdout stream. Normally Khiops
    should not write to this stream but MPI, filesystems plugins or debug versions may do it. The
    stream is captured with a UTF-8 encoding and replacing encoding errors. If equal to "" then it
    writes no file.
stderr_file_path : str, default ""
    *Advanced* Path to a file where the Khiops process writes its stderr stream. Normally Khiops
    should not write to this stream but MPI, filesystems plugins or debug versions may do it. The
    stream is captured with a UTF-8 encoding and replacing encoding errors. If equal to "" then it
    writes no file.
force_ansi_scenario : bool, default ``False``
    *Advanced:* If True the internal scenario generated by Khiops will force characters such as
    accentuated ones to be decoded with the UTF8->ANSI khiops transformation.
batch_mode : bool, default True
    *Deprecated* Will be removed in Khiops 11. If ``True`` activates batch mode (command line option
    ``-b`` of the desktop app).

.. _core-api-input-types:

khiops.core.api input types
=================================

The types accepted in most methods and classes of `khiops.core` are flexible:

- ``str`` can be replaced by ``bytes``

  - This adds flexibility for file paths and automatically created variable names (data-dependent).

- `list` can be replaced by any class implementing the `collections.abc.Sequence` interface except
  ``str`` and ``bytes``.
- `dict` can be replaced by any class implementing the `collections.abc.Mapping` interface.

.. _core-api-sampling-mode:

khiops.core.api database sampling
=================================

Several `khiops.core.api` functions can operate on dataset *samples* instead of the full datasets.
This sampling behavior is fully customizable by the user: one can specify that the function
operates on the specified sample or on its *complement*.

The sampling behavior is controlled with two parameters:

- ``sample_percentage``: A real number between 0 and 100 specifying the percentage of the data to be
  used as sample.

- ``sampling_mode``: A string specifying the sampling operation mode:

  - "Include sample": The sample consist on ``sample_percentage`` percent of the individuals in the
    dataset.

  - "Exclude sample": The sample consist on ``100 - sample_percentage`` percent of the individuals
    in the dataset. The sample is exactly the *complement* of that obtained with "Include sample".


In the case of the `~khiops.core.api.train_predictor` function the additional boolean parameter
``use_complement_as_test`` specifies whether the complement of the selected sample is used to
evaluate the trained predictor.

An Example
----------
If in the `~khiops.core.api.train_predictor` call we set:

- ``sample_percentage`` to 20
- ``sampling_mode`` to "Exclude sample"
- ``use_complement_as_test`` to ``True``

specifies a 20-80 split of the dataset. Since ``sample_mode`` is "Exclude sample" the predictor will
be trained on the 80 % part. The remaining 20 % will be used to evaluate the predictor's performance
because ``use_complement_as_test`` is ``True``.

Khiops JSON Files
=================

Generalities
------------

The structure of the Khiops JSON files is self-documented:

- Most of the information is available as key-value pairs, where the keys resemble the labels used
  in Khiops' classic report files (tab-separated plain-text files with extension ``.xls``) or
  dictionary files.
- In order to be human-readable the files are *beautified* with a comfortable spacing and
  indentation.

Structure and Performance
-------------------------

The Khiops JSON files may be large (tens of MB) when analyzing datasets with many columns, or when
specifying the creation of thousands of variables in the multi-table case. To handle these
situations, the report attributes in the JSON file are sorted by increasing size, thus easing the
use of streaming parsers.

Furthermore, memory-scalable parsing techniques can be implemented. For example, the heavier parts
of the file can be separated and split into chunks. Then, these chunks can be indexed using the
information found at the top of the report, allowing the on-demand access to the detailed parts of
the report.

Khiops Report Files Structure (.khj)
------------------------------------

At the top level the order is as follows:

- Modeling report
- Evaluation report(s)
- Preparation report(s)

The preparation reports are at the end because they can be very large when many
variables are analyzed.

Each report field is organized in three sections:

- Summary: General (short) information about the report
- A list of report items:

  - Variable statistics (preparation), trained predictor (modeling) and predictor
    performance (evaluation)
  - Each item has a "Rank"

    - Example: The second most informative variable has the categorical rank "R02"

  - Each item is described by a few summary attributes

- A dictionary of detailed report items. The keys of this dictionary are the
  previously mentioned "Rank" attributes. Note that:

  - Not all report items are detailed
  - The detailed information may be large (example: data grid).


