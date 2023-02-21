######################################################################################
# Copyright (c) 2018 - 2023 Orange - All Rights Reserved                             #
# * This software is the confidential and proprietary information of Orange.         #
# * You shall not disclose such Restricted Information and shall use it only in      #
#   accordance with the terms of the license agreement you entered into with Orange  #
#   named the "Khiops - Python Library Evaluation License".                          #
# * Unauthorized copying of this file, via any medium is strictly prohibited.        #
# * See the "LICENSE.md" file for more details.                                      #
######################################################################################
"""Helper functions for specific and/or advanced treatments"""
import os

from pykhiops.core import api
from pykhiops.core import filesystems as fs
from pykhiops.core.api_internals.runner import get_runner
from pykhiops.core.common import (
    create_unambiguous_khiops_path,
    is_list_like,
    type_error_message,
)
from pykhiops.core.dictionary import DictionaryDomain, read_dictionary_file


def deploy_coclustering(
    dictionary_file_path_or_domain,
    dictionary_name,
    data_table_path,
    coclustering_file_path,
    key_variable_names,
    deployed_variable_name,
    results_dir,
    detect_format=True,
    header_line=None,
    field_separator=None,
    output_header_line=True,
    output_field_separator="\t",
    max_preserved_information=0,
    max_cells=0,
    max_part_numbers=None,
    build_cluster_variable=True,
    build_distance_variables=False,
    build_frequency_variables=False,
    variables_prefix="",
    results_prefix="",
    batch_mode=True,
    log_file_path=None,
    output_scenario_path=None,
    task_file_path=None,
    trace=False,
):
    r"""Deploys an *individual-variable* coclustering on a data table

    This procedure generates the following files in ``results_dir``:
        - ``Coclustering.kdic``: A multi-table dictionary file for further deployments
          of the coclustering with deploy_model
        - ``Keys<data_table_file_name>``: A data table file containing only the keys of
          individual
        - ``Deployed<data_table_file_name>``: A data table file containing the deployed
          coclustering model

    Parameters
    ----------
    dictionary_file_path_or_domain : str or `.DictionaryDomain`
        Path of a Khiops dictionary file or a DictionaryDomain object.
    dictionary_name : str
        Name of the dictionary to be analyzed.
    data_table_path : str
        Path of the data table file.
    coclustering_file_path : str
        Path of the coclustering model file (extension ``.khc`` or ``.khcj``)
    key_variable_names : list of str
        Names of the variables forming the unique keys of the individuals.
    deployed_variable_name : str
        Name of the coclustering variable to deploy.
    results_dir : str
        Path of the results directory.
    detect_format : bool, default ``True``
        If True detects automatically whether the data table file has a header and its
        field separator. It's ignored if ``header_line`` or ``field_separator`` are set.
    header_line : bool, optional (default ``True`` if ``detect_format`` is False)
        If True it uses the first line of the data as column names. Overrides
        ``detect_format`` if set.
    field_separator : str, optional (default "\\t" if ``detect_format`` is False)
        A field separator character, overrides ``detect_format`` if set ("" counts
        as "\\t").
    output_header_line : bool, default ``True``
        If True writes a header line containing the column names in the output table.
    output_field_separator : str, default "\\t"
        A field separator character (empty string counts as tab).
    max_preserved_information : int, default 0
        Maximum information preserve in the simplified coclustering. If equal to 0 there
        is no limit.
    max_cells : int, default 0
        Maximum number of cells in the simplified coclustering. If equal to 0 there is
        no limit.
    max_part_numbers : dict, optional
      Dictionary associating variable names to their maximum number of parts to
      preserve in the simplified coclustering. For variables not present in
      ``max_part_numbers`` there is no limit.
    build_cluster_variable : bool, default ``True``
        If True includes a cluster id variable in the deployment.
    build_distance_variables : bool, default False
        If True includes a cluster distance variable in the deployment.
    build_frequency_variables : bool, default False
        If True includes the frequency variables in the deployment.
    variables_prefix : str, default ""
        Prefix for the variables in the deployment dictionary.
    results_prefix : str, default ""
        Prefix of the result files.
    ... :
        Options of the `.PyKhiopsRunner.run` method from the class `.PyKhiopsRunner`.

    Returns
    -------
    tuple
        A 2-tuple containing:

        - The deployed data table path
        - The deployment dictionary file path.

    Raises
    ------
    `TypeError`
        Invalid type ``dictionary_file_path_or_domain`` or ``key_variable_names``
    `ValueError`
        If the type of the dictionary key variables is not equal to ``Categorical``

    Examples
    --------
    See the following function of the ``samples.py`` documentation script:
        - `samples.deploy_coclustering()`
    """
    # Obtain the dictionary of the table where the coclustering variables are
    api.check_dictionary_file_path_or_domain(dictionary_file_path_or_domain)
    if isinstance(dictionary_file_path_or_domain, DictionaryDomain):
        domain = dictionary_file_path_or_domain
    else:
        domain = read_dictionary_file(dictionary_file_path_or_domain)

    # Disambiguate the results directory path if necessary
    results_dir = create_unambiguous_khiops_path(results_dir)

    # Check the type of non basic keyword arguments specific to this function
    if not is_list_like(key_variable_names):
        raise TypeError(
            type_error_message("key_variable_names", key_variable_names, "ListLike")
        )

    # Detect the format once and for all to avoid inconsistencies
    if detect_format and header_line is None and field_separator is None:
        header_line, field_separator = api.detect_data_table_format(
            data_table_path, dictionary_file_path_or_domain, dictionary_name
        )
    else:
        if header_line is None:
            header_line = True
        if field_separator is None:
            field_separator = "\t"

    # Access the dictionary in the relevant variables
    dictionary = domain.get_dictionary(dictionary_name)

    # Verify that the key variables are categorical
    for key_variable_name in key_variable_names:
        key_variable = dictionary.get_variable(key_variable_name)
        if key_variable.type != "Categorical":
            raise ValueError(
                "key variable types must be 'Categorical', "
                f"variable '{key_variable_name}' has type '{key_variable.type}'"
            )
    # Make a copy of the dictionary and set the id_variable as key
    tmp_dictionary = dictionary.copy()
    tmp_dictionary.key = key_variable_names
    tmp_domain = DictionaryDomain()
    tmp_domain.add_dictionary(tmp_dictionary)
    tmp_dictionary_path = get_runner().create_temp_file(
        "_deploy_coclustering_", ".kdic"
    )

    # Create a root dictionary containing the keys
    root_dictionary_name = "CC_" + dictionary_name
    table_variable_name = "Table_" + dictionary_name
    api.build_multi_table_dictionary(
        tmp_domain, root_dictionary_name, table_variable_name, tmp_dictionary_path
    )

    # Create the deployment dictionary
    api.prepare_coclustering_deployment(
        tmp_dictionary_path,
        root_dictionary_name,
        coclustering_file_path,
        table_variable_name,
        deployed_variable_name,
        results_dir,
        max_preserved_information=max_preserved_information,
        max_cells=max_cells,
        max_part_numbers=max_part_numbers,
        build_cluster_variable=build_cluster_variable,
        build_distance_variables=build_distance_variables,
        build_frequency_variables=build_frequency_variables,
        variables_prefix=variables_prefix,
        results_prefix=results_prefix,
        batch_mode=batch_mode,
        log_file_path=log_file_path,
        output_scenario_path=output_scenario_path,
        task_file_path=task_file_path,
        trace=trace,
    )

    # Extract the keys from the tables to a temporary file
    data_table_file_name = os.path.basename(data_table_path)
    keys_table_file_path = fs.get_child_path(results_dir, f"Keys{data_table_file_name}")
    api.extract_keys_from_data_table(
        tmp_dictionary_path,
        dictionary_name,
        data_table_path,
        keys_table_file_path,
        header_line=header_line,
        field_separator=field_separator,
        output_header_line=header_line,
        output_field_separator=field_separator,
        trace=trace,
    )

    # Deploy the coclustering model
    coclustering_dictionary_file_path = fs.get_child_path(
        results_dir, "Coclustering.kdic"
    )
    output_data_table_path = fs.get_child_path(
        results_dir, f"Deployed{data_table_file_name}"
    )
    additional_data_tables = {
        f"{root_dictionary_name}`{table_variable_name}": data_table_path
    }
    api.deploy_model(
        coclustering_dictionary_file_path,
        root_dictionary_name,
        keys_table_file_path,
        output_data_table_path,
        header_line=header_line,
        field_separator=field_separator,
        output_header_line=output_header_line,
        output_field_separator=output_field_separator,
        additional_data_tables=additional_data_tables,
        trace=trace,
    )
    return output_data_table_path, coclustering_dictionary_file_path


def deploy_predictor_for_metrics(
    dictionary_file_path_or_domain,
    dictionary_name,
    data_table_path,
    output_data_table_path,
    detect_format=True,
    header_line=None,
    field_separator=None,
    sample_percentage=70,
    sampling_mode="Include sample",
    additional_data_tables=None,
    output_header_line=True,
    output_field_separator="\t",
    trace=False,
):
    r"""Deploys the necessary data to estimate the performance metrics of a predictor

    For each instance for each instance it deploys:

    - The true value of the target variable
    - The predicted value of the target variable
    - The probabilities of each value of the target variable *(classifier only)*

    .. note::
        To obtain the data of the default Khiops test dataset use ``sample_percentage =
        70`` and ``sampling_mode = "Exclude sample"``.

    Parameters
    ----------
    dictionary_file_path_or_domain : str or `.DictionaryDomain`
        Path of a Khiops dictionary file or a DictionaryDomain object.
    dictionary_name : str
        Name of the predictor dictionary.
    data_table_path : str
        Path of the data table file.
    output_data_table_path : str
        Path of the scores output data file.
    detect_format : bool, default ``True``
        If True detects automatically whether the data table file has a header and its
        field separator. It's ignored if ``header_line`` or ``field_separator`` are set.
    header_line : bool, optional (default ``True`` if ``detect_format`` is ``False``)
        If True it uses the first line of the data as column names. Overrides
        ``detect_format`` if set.
    field_separator : str, optional (default "\\t" if ``detect_format`` is ``False``)
        A field separator character, overrides ``detect_format`` if set ("" counts
        as "\\t").
    sample_percentage : int, default 70
        See ``sampling_mode`` option below.
    sampling_mode : "Include sample" or "Exclude sample"
        If equal to "Include sample" deploys the predictor on ``sample_percentage``
        percent of data and if equal to "Exclude sample" on the complementary ``100 -
        sample_percentage`` percent of data.
    additional_data_tables : dict, optional
        A dictionary containing the data paths and file paths for a multi-table
        dictionary file. For more details see :doc:`/multi_table_tasks` documentation.
    output_header_line : bool, default ``True``
        If True writes a header line containing the column names in the output table.
    output_field_separator : str, default "\\t"
        A field separator character ("" counts as "\\t").
    ... :
        Options of the `.PyKhiopsRunner.run` method from the class `.PyKhiopsRunner`.
    """
    # Check the dictionary domain
    api.check_dictionary_file_path_or_domain(dictionary_file_path_or_domain)

    # Load the dictionary file into a domain if necessary
    if isinstance(dictionary_file_path_or_domain, DictionaryDomain):
        predictor_domain = dictionary_file_path_or_domain.copy()
    else:
        predictor_domain = read_dictionary_file(dictionary_file_path_or_domain)

    # Check that the specified dictionary is a predictor
    predictor_dictionary = predictor_domain.get_dictionary(dictionary_name)
    if "PredictorType" not in predictor_dictionary.meta_data:
        raise ValueError(f"Dictionary '{predictor_dictionary.name}' is not a predictor")

    # Set the type of classifier
    predictor_type = predictor_dictionary.meta_data.get_value("PredictorType")
    is_classifier = predictor_type == "Classifier"

    # Use the necessary columns
    predictor_dictionary.use_all_variables(False)
    for variable in predictor_dictionary.variables:
        if "TargetVariable" in variable.meta_data:
            variable.used = True
        elif is_classifier:
            if "Prediction" in variable.meta_data:
                variable.used = True
            for key in variable.meta_data.keys:
                if key.startswith("TargetProb"):
                    variable.used = True
        elif not is_classifier and "Mean" in variable.meta_data:
            variable.used = True

    # Deploy the scores
    api.deploy_model(
        predictor_domain,
        dictionary_name,
        data_table_path,
        output_data_table_path,
        detect_format=detect_format,
        header_line=header_line,
        field_separator=field_separator,
        sample_percentage=sample_percentage,
        sampling_mode=sampling_mode,
        additional_data_tables=additional_data_tables,
        output_header_line=output_header_line,
        output_field_separator=output_field_separator,
        trace=trace,
    )
