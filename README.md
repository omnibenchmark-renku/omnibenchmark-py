# Omnibenchmark

Generate and manage omnibenchmark modules for open and continuous benchmarking.
Each module represents a single building block of a benchmark, e.g., dataset, method, metric.
Omnibenchmark-py provides a structure to generate modules and automatically run them.

![](omni.svg)

## Installation

You can install **omnibenchmark** from [PyPI](https://pypi.org/project/omnibenchmark/):

```sh
pip install omnibenchmark
```

The module is supported on Python >= 3.8 and requires [renku >= 1.5.0](https://pypi.org/project/renku/).

## How to use omnibenchmark

For a detailed documentation and tutorials check the [omnibenchmark documentation](https://omnibenchmark.readthedocs.io).

### Quick start

Omnibenchmark uses the `renku` platform to run open and continous benchmarks. To contribute an independent module to one of the existing benchmarks please start by creating a new [renku project](#Create-a-new-renku-project). Each module consist of a Docker image, that defines it's environment, a dataset to store outputs and metadata, a workflow that describes how to generate outputs and input and parameter datasets with input files and parameter definitions, if they are used. Thus each module is an independent benchmark part and can be run, used and modified independently as such. Modules are connected by importing (result) datasets from other modules as input datasets and will automatically be updated according to them.   
All relevant information on how to run a specific module are stored as [`OmniObject`](#omnibenchmark-classes).
The most convinient way to generate an instance of an `OmniObject` is to build it from an `config.yaml` file:

``` python
## modules
from omnibenchmark.utils.build_omni_object import get_omni_object_from_yaml

## Load object
omni_obj = get_omni_object_from_yaml('src/config.yaml')

```

The `config.yaml` defines all module specific information as inputs, outputs, script to run the module, benchmark that the module belongs to and much more. A simple `config.yaml` file could look like this. Please check section [The config.yaml file](#the-config.yaml-file) for more details.

```sh
---
data:
    name: "module-name"
    title: "A new module"
    description: "A new module for omnibenchmark, e.g., a dataset, method, metric,..."
    keywords: ["module-type-key"]
script: "path/to/module_script"
outputs:
    template: "data/${name}/${name}_${out_name}.${out_end}"
    files:
        counts: 
            end: "mtx.gz"
        data_info:
            end: "json"
        meta:
            end: "json"
benchmark_name: "an-omnibenchmark"
```
Once you have an instance of an `OmniObject` you can check, if it looks as you expected like this:

```python
## Check object
print(omni_obj.__dict__)
print(omni_obj.outputs.file_mapping)
print(omni_obj.command.command_line)
``` 

If all inputs, outputs and the command line call look as you expected you can run your module:

```python
## create output dataset that stores all result/output files
omni_obj.create_dataset()

## Update inputs from other modules 
omni_obj.update_obj()

## Run your script with all defined inputs and outputs.
## This also generates a workflow description (plan) and is tracked as activity.
omni_obj.run_renku()

## Link output files to output dataset 
omni_obj.update_result_dataset()

## Save and commit to gitlab
renku_save()
```
Once these steps ran successfully and your outputs were generated the module is ready to be [submitted to become a part of omnibenchmark](#Submit-your-module).

### What is renku?
[Renku](https://renkulab.io) is a platform and tools for reproducible and collaborative data analysis from the [Swiss Data Science Centre](https://datascience.ch/). Besides other functionalities renku provides a framework to create and run data analysis projects, which come with their own Docker container, datasets and workflows. By storing the metadata of projects and datasets on a knowledge graph renku facilitates provenance tracking and project interactions. To do so renku combines a set of microservices:
- GitLab, for version control and project management
- GitLFS, for file storage
- Kubernetes/Docker, to manage containerized environment
- Jupyter server, to provide interactive sessions
- Apache Jena, to generate, store and manage triplets and the triplet store (knowledge graph) 

Details on how to use renku can be found in their [Documentation](https://renku.readthedocs.io/en/latest/index.html). Omnibenchmark uses renku to build and run collaborative and continuous benchmarks. 

#### Create a new renku project
Omnibenchmark modules are build as separate renku projects. Contributions to one of the existing benchmarks start by creating a new project using the [renku platform](https://renkulab.io). This can be done by registering directly or using a Github account, an Orchid or a Switch-EDU ID.
A new project can be created by a few clicks as described [here](https://renku.readthedocs.io/en/latest/tutorials/first_steps/01_create_project.html). Templates can be chosen depending on the projects code or the Basic Python template. Project can then be populated/changed in an interactive renku session (see session tab of the project) or within the GitLab instance or clone of the project (Overview tab --> View in GitLab). 

### Project requirements
Project requirements can be defined by adapting the `Dockerfile` and specifying the all required R packages with their versions in the `install.R` file and all required python modules with their versions in the `requirements.txt` file. The later needs to contain at least `omnibenchmark`. If you work in an interactive session you need to save/commit your changes either by running `renku save` or `git add/commit/push` and close and restart the session once the new Docker image has been build. The built is triggered automatically when commiting changes, but can take a while depending on the requirments. 

### The config.yaml file
Usually all specific information about a benchmark project can be specified in a `config.yaml` file. Below we show an example with all standard fields and explanations to them. Many fields are optional and do not apply to all modules. All unneccessary fields can be skipped. There are further optional fields for specfic edge cases, that are described in an extra `config.yaml` file. In general the `config.yaml` file consists of a data, an input, an output and a parameter section as well as a few extra fields to define the main benchmark script and benchmark type. Except for the data section the other sections are optional. Multiple values can be parsed as Lists. 

```yaml
# Data section to describe the object and the associated (result) dataset
data:
    # Name of the dataset
    name: "out_dataset"
    # Title of the dataset (Optional)
    title: "Output of an example OmniObject"
    # Description of the dataset (Optional)
    description: "This dataset is supposed to store the output files from the example omniobject"
    # Dataset keyword(s) to make this dataset reachable for other projects/benhcmark components
    keywords: ["example_dataset"]
# Script to be run by the workflow associated to the project
script: "path/to/method/dataset/metric/script.py"
# Interpreter to run the script (Optional, automatic detection)
interpreter: "python"
# Benchmark that the object is associated to.
benchmark_name: "omni_celltype"
# Orchestrator url of the benchmark (Optional, automatic detection)
orchestrator: "https://www.orchestrator_url.com"
# Input section to describe output file types. (Optional)
inputs:
    # Keyword to find input datasets, that shall be imported 
    keywords: ["import_this", "import_that"]
    # Input file types
    files: ["count_file", "dim_red_file"]
    # Prefix (part of the filename is sufficient) to automatically detect file types by their names
    prefix:
        count_file: "counts"
        dim_red_file: ["features", "genes"]
# Output section to describe output file types. (Optional)
outputs:
    # Output filetypes and their endings
    files:
        corrected_counts: 
            end: ".mtx.gz"
        meta:
            end: ".json"
# Parameter section to describe the parameter dataset, values and filter. (Optional)
parameter:
    # Names of the parameter to use
    names: ["param1", "param2"]
    # Keyword(s) used to import the parameter dataset
    keywords: ["param_dataset"]
    # Filter that specify limits, values or combinations to exclude
    filter:
        param1:
            upper: 50
            lower: 3
            exclude: 12
    param2:
        "path/to/file/with/parameter/combinations/to/exclude.json"
```

Specific fields, that are only relevant for edge cases. These fields have their counterparts in the generated [OmniObject](#omnibenchmark-classes).
Changes of the attributes of the OmniObject instance have the same effects, but come with the flexibility of python code. 

```yaml
# Command to generate the workflow with (Optional, automatic detection)
command_line: "python path/to/method/dataset/metric/script.py --count_file data/import_this_dataset/...mtx.gz"
inputs:
    # Datasets and manual file type specifications (automatic detection!)
    input_files:
        import_this_dataset:
            count_file: "data/import_this_dataset/import_this_dataset__counts.mtx.gz"
            dim_red_file: "data/import_this_dataset/import_this_dataset__dim_red_file.json"
    # (Dataset) name that default input files belong to (Optional, automatic detection)
    default: "import_this_dataset"
    # Input dataset names that should be ignored (even if they have one of the specified input keywords assciated)
    filter_names: ["data1", "data2"]
outputs:
    # Template to automatically generate output filenames (Optional - recommended for advanced user only)
    template: "data/${name}/${name}_${unique_values}_${out_name}.${out_end}"
    # Variables used for automatic output filename generation (Optional - recommended for advanced user only)
    template_vars:
        vars1: "random"
        vars2: "variable"
    # Manual specification of mapping for output files and their corresponding input files and parameter values (automatic detection!)
    file_mapping:
        mapping1: 
            output_files:
                corrected_counts: "data/out_dataset/out_dataset_import_this__param1_10__param2_test_corrected_counts.mtx.gz"
                meta: "data/out_dataset/out_dataset_import_this__param1_10__param2_test_meta.json"
        input_files:
            count_file: "data/import_this_dataset/import_this_dataset__counts.mtx.gz"
            dim_red_file: "data/import_this_dataset/import_this_dataset__dim_red_file.json"
        parameter:
            param1: 10
            param2: "test"
    # Default output files (Optional, automatic detection)
    default:
        corrected_counts: "data/out_dataset/out_dataset_import_this__param1_10__param2_test_corrected_counts.mtx.gz"
        meta: "data/out_dataset/out_dataset_import_this__param1_10__param2_test_meta.json"
parameter:
    default:
        param1: 10
        param2: "test"
```

### Omnibenchmark classes
Classes to manage omnibenchmark modules and their interactions. The main class is the [OmniObject](#omniobject), that consollidates all relevant information and functions of a module. This object has further subclasses that define inputs, outputs, commands and the workflow. 

---

#### OmniObject
Main class to manage an omnibenchmark module. 
It takes the following arguments:
* **`name (str)`**: Module name 
* **`keyword (Optional[List[str]], optional)`**: Keyword associated to the modules output dataset.
* **`title (Optional[str], optional)`**: Title of the modules output dataset.
* **`description (Optional[str], optional)`**: Description of the modules output dataset.
* **`script (Optional[PathLike], optional)`**: Script to generate the modules workflow for.
* **`command (Optional[OmniCommand], optional)`**: Workflow command - will be automatically generated if missing.
* **`inputs (Optional[OmniInput], optional)`**: Definitions of the workflow inputs.
* **`parameter (Optional[OmniParameter], optional)`**: Definitions of the workflow parameter.
* **`outputs (Optional[OmniOutput], optional)`**: Definitions of the workflow outputs.
* **`omni_plan (Optional[OmniPlan], optional)`**: The workflow description.
* **`benchmark_name (Optional[str], optional)`**: Name of the benchmark the module is associated to.
* **`orchestrator (Optional[str], optional)`**: Orchestrator url of the benchmark th emodule is associated to. Automatic detection.
* **`wflow_name (Optional[str], optional)`**: Workflow name. Will be set to the module name if none.
* **`dataset_name (Optional[str], optional)`**: Dataset name. Will be set to the module name if none.

The following class methods can be run on an instance of an OmniObject:
* **`create_dataset()`**: Method to create a renku dataset with the in the object specified attributes in the current renku project. 
* **`update_object()`**: Method to check for new imports or updates in input and the parameter datasets. Will update object attributes accordingly.
* **`run_renku()`**: Method to generate and update the workflow and all output files as specified in the object.
* **`update_result_dataset()`**: Method to update and add all output datasets to the dataset specified in the object.

---

#### OmniInput
Class to manage inputs of an omnibenchmark module.
This class has the following attributes:
* **`names (List[str])`**: Names of the input filetypes
* **`prefix (Optional[Mapping[str, List[str]]], optional)`**: Prefixes (or substrings) of the input filetypes.
* **`input_files (Optional[Mapping[str, Mapping[str, str]]], optional)`**: Input files ordered by file types.
* **`keyword (Optional[List[str]], optional)`**: Keyword to define which datasets are imported as input datasets.
* **`default (Optional[str], optional)`**: Default input name (e.g., dataset).
* **`filter_names (Optional[List[str]], optional)`**: Input dataset names to be ignored.

The following class methods can be run on an instance of an OmniInput:
* **`update_inputs()`**: Method to import new and update existing input datasets and update the object accordingly

---

#### OmniOutput
Class to manage outputs of an omnibenchmark module. 
This class has the following attributes:
* **`name (str)`**: Name that is specific for all outputs. Typically the module name/OmniObject name.
* **`out_names (List[str])`**: Names of the output file types
* **`output_end (Optional[Mapping[str, str]], optional)`**: Endings of the output filetypes.
* **`out_template (str, optional)`**: Template to generate output file names.
* **`file_mapping (Optional[List[OutMapping]], optional)`**: Mapping of input files, parameter values and output files.
* **`inputs (Optional[OmniInput], optional)`**: Object specifying all valid inputs.
* **`parameter (Optional[OmniParameter], optional)`**: Object speccifying the parameter space.
* **`default (Optional[Mapping], optional)`**: Default output files.
* **`template_fun (Optional[Callable[..., Mapping]], optional)`**: Function to use to automatically generate output filenames.
* **`template_vars (Optional[Mapping], optional)`**: Variables that are used by template_fun.

The following class methods can be run on an instance of an OmniInput:
* **`update_outputs()`**: Method to update the output definitions according to the objects attributes.

---

#### OmniParameter
Class to manage parameter of an omnibenchmark module.
This class has the following attributes:
* **`names (List[str])`**: Name of all valid parameter
* **`values (Optional[Mapping[str, List]], optional)`**: Parameter values - usually automatically detected.
* **`default (Optional[Mapping[str, str]], optional)`**: Default parameter values.
* **`keyword (Optional[List[str]], optional)`**: Keyword to import the parameter dataset with.
* **`filter (Optional[Mapping[str, str]], optional)`**: Filter to use for the parameter space.
* **`combinations (Optional[List[Mapping[str, str]]], optional)`**: All possible parameter combinations.

The following class methods can be run on an instance of an OmniInput:
* **`update_parameter()`**: Method to import and update parameter datasets and update the object/parameter space accordingly.

---

#### OmniCommand
Class to manage the main workflow command of an omnibenchmark module. 
This class has the following attributes:
* **`script (Union[PathLike, str])`**: Path to the script run by the command
* **`interpreter (str, optional)`**: Interpreter to run the script with.
* **`command_line (str, optional)`**: Command line to be run.
* **`outputs (OmniOutput, optional)`**: Object specifying all outputs.
* **`input_val (Optional[Mapping], optional)`**: Input file tyoes and paths to run the command on.
* **`parameter_val (Optional[Mapping], optional)`**: Parameter names and values to run the command with.

The following class methods can be run on an instance of an OmniInput:
* **`update_command()`**: Method to update the command according to the outputs,inputs,parameter.

---

#### OmniPlan
Class to manage the workflow of an omnibenchmark module. 
This class has the following attributes:

* **`plan (PlanViewModel)`**: A plan view model as defined in renku
* **`param_mapping (Optional[Mapping[str, str]], optional)`**: A mapping between the component names of the plan and the OmniObject.

The following class methods can be run on an instance of an OmniInput:
* **`predict_mapping_from_file_dict()`**: Method to predict the mapping from the (input-, output-, parameter) file mapping used to generate the command.

---

### Submit your module
Once a module is complete and works it can be included into the omnibenchmark orchestrator of the associated benchmark. This means it will be automatically run, continously updated and it's result will automatically be used as inputs by downstream modules. Please open an issue on the corresponding orchestrator GitLab project linking to the project to get the project taken up. 
You can find the corresponding GitLab project at the [omnibenchmark website](https://omnibenchmark.pages.uzh.ch/omni_dash/benchmarks/).


## Release History
* 0.0.13
    * Add function docstrings
    * Add name filter for importing input datasets
    * Add Documentation in Readme
    * FIX:
    * Adapt renku_update_activities to handle skip_update_metadata argument in renku 1.5.0
* 0.0.12
    * FIX:
    * accept float as parameter values and keep after filtering  
* 0.0.9
    * FIX:
    * add common sequence to auto file matching  
* 0.0.8
    * FIX:
    * add update command to omni_obj.update_object()  
* 0.0.4 - 0.0.7
    * FIX:
    * convert defaults to string to generate plan 
    * adapt output default
    * dependency between command line call and renku input definitions
    * ignore not existing defaults
* 0.0.3
    * FIX:
    * automatic input detection from prefixes for files from the same dataset 
* 0.0.2
    * FIX:
    * automatic command detection, file_mapping.input_files structure
* 0.0.1
    * First version of all main functionalities

## Meta

Almut Lütge – [@Almut30618742](https://twitter.com/Almut30618742)
Anthony Sonrel – [@AnthonySonrel](https://twitter.com/AnthonySonrel)
Mark Robinson – [@markrobinsonca](https://twitter.com/markrobinsonca)

Distributed under the Apache 2.0 license. See ``LICENSE`` for more information.

[https://github.com/almutlue/omnibenchmark-py](https://github.com/almutlue/omnibenchmark-py)

## Contributing

1. Fork it (<https://github.com/almutlue/omnibenchmark-py/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
