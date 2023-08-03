# Net-Manage

Net-Manage is a Python-based project that serves as a framework for other applications. It primarily focuses on collecting data and integrating disparate systems. It is designed for usage on Ubuntu 20.04, Python 3.8-3.10, and requires build-essentials. While it has been known to work on Mac and Windows (using Windows Subsystem for Linux), these platforms are not officially supported.

## Requirements

1. Ubuntu 20.04
2. Python 3.8 - 3.10
3. build-essentials

## Quick Start

Here's a quick guide to get you started:

1. **Install Git and build-essentials**

```sudo apt updat
sudo apt upgrade
sudo apt install git build-essentials
```

1. **Clone the repository**

    Using git, you can clone the repository to your local machine:

    ```bash
    git clone https://github.com/InsightSSG/Net-Manage.git
    ```

2. **Create a Python virtual environment**

    Navigate to the project folder and create a new virtual environment. You can do this with either `venv` or `miniconda`.

    - Using `venv`:
    ```bash
    cd Net-Manage
    python3 -m venv venv
    ```

    - Using `miniconda`:
    ```bash
    cd Net-Manage
    conda create --name myenv
    ```

3. **Activate the virtual environment**

    - For `venv`, use the following command:

    ```bash
    source venv/bin/activate
    ```

    - For `miniconda`, use the following command:

    ```bash
    conda activate myenv
    ```

4. **Install the requirements**

    The required Python libraries can be installed using pip:

    ```bash
    pip install -r requirements.txt
    ```

5. **Run Jupyter Lab**

    Start Jupyter Lab using the following command:

    ```bash
    jupyter-lab
    ```

6. **Configure Environment Variables**

    1. For non-Streamlit files:
        Environment variables are stored in the .env file. Simply rename `.env_example` to `.env`. If you do not need to use a variable, leave it empty.

    2. For Streamlit files:
        Environment variables for Streamlit files are stored in `.streamlit/secrets.toml`. The formatting is largely the same. Simply re-name `.secrets/secrets_example.tml` to `.secrets/secrets.toml` and enter any variables you need to use.

7. **Open Net-Manage.ipynb**

    In the Jupyter Lab interface, navigate to the location of `net-manage.ipynb` file and click to open it.

## Full Documentation

For a comprehensive guide on the usage and functionalities of Net-Manage, refer to our Full Documentation in the html directory of the repository.

### Table of Contents

- **[Collectors](./html/collectors/index.html)**
  - [Cisco ASA Collectors](./html/collectors/cisco_asa_collectors.html)
  - [Cisco IOS Collectors](./html/collectors/cisco_ios_collectors.html)
  - [Cisco NXOS Collectors](./html/collectors/cisco_nxos_collectors.html)
  - [DNAC Collectors](./html/collectors/dnac_collectors.html)
  - [F5 Collectors](./html/collectors/f5_collectors.html)
  - [Infoblox NIOS Collectors](./html/collectors/infoblox_nios_collectors.html)
  - [Meraki Collectors](./html/collectors/meraki_collectors.html)
  - [Netbox Collectors](./html/collectors/netbox_collectors.html)
  - [Palo Alto Collectors](./html/collectors/palo_alto_collectors.html)
  - [SolarWinds Collectors](./html/collectors/solarwinds_collectors.html)

- **[Helpers](./html/helpers/index.html)**
  - [Helpers](./html/helpers/helpers.html)
  - [Netbox Helpers](./html/helpers/netbox_helpers.html)
  - [Report Helpers](./html/helpers/report_helpers.html)

- **[Run Collectors](./html/run_collectors.html)**
- **[Setup](./html/setup.html)**
- **[Validators](./html/validators.html)**

## Platform Support

Net-Manage is designed and tested for usage on Ubuntu 20.04 with Python 3.8-3.10. However, it has been known to work on other platforms such as MacOS and Windows (using the Windows Subsystem for Linux), but please note that these are not officially supported platforms. For any issues encountered during installation or usage on unsupported platforms, we will not be able to provide any official support.

## Contact

For further queries, please raise an issue on the repository.
