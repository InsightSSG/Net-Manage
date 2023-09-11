# Net-Manage

Net-Manage is a Python-based project that serves as a framework for other applications. It is extensible and functional, making it easy to import some or all of its functionality into other scripts and applications.

It primarily focuses on collecting data and integrating disparate systems. It is designed for usage on Ubuntu 20.04, Python 3.8-3.10, and requires build-essentials. While it has been known to work on Mac and Windows (using Windows Subsystem for Linux), these platforms are not officially supported.

## Requirements

1. Ubuntu 20.04
2. Python 3.8 - 3.10
3. build-essential

## Quick Start

Here's a quick guide to get you started:

1. **Install Git and build-essentials**

```sudo apt update
sudo apt upgrade
sudo apt install git build-essential -y
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
  - [F5 Helpers](./html/helpers/f5_helpers.html)
  - [Netbox Helpers](./html/helpers/netbox_helpers.html)
  - [Obfuscate Addresses](./html/helpers/obfuscate_addresses.html)
  - [Report Helpers](./html/helpers/report_helpers.html)

- **[Parsers](./html/parsers/index.html)**
  - [Cisco ASA Parsers](./html/parsers/cisco_asa_parsers.html)
  - [Cisco IOS Parsers](./html/parsers/cisco_ios_parsers.html)
  - [Cisco NXOS Parsers](./html/parsers/cisco_nxos_parsers.html)
  - [F5 Parsers](./html/parsers/f5_parsers.html)
  - [Palo Alto Parsers](./html/parsers/palo_alto_parsers.html)

- **[Updaters](./html/updaters/index.html)**
  - [Netbox Updaters](./html/updaters/netbox_updaters.html)

- **[Writers](./html/writers/index.html)**
  - [Cisco NXOS Writers](./html/writers/cisco_nxos_writers.html)
  - [Netbox Writers](./html/writers/netbox_writers.html)

- **[Run Collectors](./html/run_collectors.html)**
- **[Setup](./html/setup.html)**
- **[Validators](./html/validators.html)**

## Background

There is no shortage of frameworks, APIs, tools and scripts for managing IT networks. However, the fact that people must continually create more indicates that current strategies for automation are not sufficient. We feel there are three main problems in the tooling ecosystem:

1. Vendor lock. Tools work really well for a particular vendor or type of appliance, but not for anything else.
2. Lack of extensibility. It is difficult or impossible to modify tools.
3. Tools do not integrate with other tools. Most open source project maintainers do not have time or budget to extend a tool beyond their immediate needs, and vendors who create tooling do not have an incentive to make it compatible with their competitors' tools.

### Solution

The Net-Manage framework is designed to solve those problems. It is:

1. Completely modular. You will not find a single class. You will rarely find a nested function. The code is easy to understand, easy to test, and easy to debug.
2. Easy to understand. Every function has a clear purpose. Every function is well-documented. There is no data mutation or inheritance. The same input always produces the same output.
3. Vendor agnostic. Need to support F5s? Palo Altos? Cisco DNAC? Netbox? Infoblox? Meraki? Cisco IOS, ASA and NXOS? No problem. All those platforms and more are already supported, and we add additional support on a regular basis. If more functionality is needed, open a Github issue and we'll do our best to help you add it.
4. Designed from the ground up for integration. The primary purpose of this tool is to integrate with other tools. We use it to assess networks, synchronize data between systems like Netbox and Solarwinds, find correlations in data, and much more.

### What's the Catch?

There is no catch. We need the same tools that are customers need. Open source products allow us to move rapidly. We use them, so this is our way of giving back to the community.

## Philosophy

I had the good fortune of working at Microsoft from 2014 - 2021. I was in Global Network Services until 2015, when my team moved into Azure.

In the early days of Azure, our tooling was a mess. By the time I left in 2021, we had a fully automatable network. The only times we needed to make changes manually were for break/fix (and we always tried to find ways to automate the fix after the issue was mitigated).

We were doing it on our own. The tooling ecosystem that exists today just wasn't available. We made a lot of mistakes. I tried to learn from them. In light of that, I followed this philosophy when creating Net-Manage:

1. Move fast, don't break things.
    1. Facebook popularized "Move fast and break things." Venture capitalists and technologists are still obsessed with it.
    2. They do not know or do not care that Mark Zuckerburg later changed the motto to "Move fast with stable infrastructure."
    3. It's possible to move fast and *not* break things.
    4. **Key Takeaway:** Keep the code as simple and minimal as possible.
2. Debug the network, not the code.
    1. If there is an outage, you need to be confident your code did not cause it.
    2. If your code is helping troubleshoot an outage, you need to be confident in its output.
    3. **Key Takeaway:** Test and document your code.
3. Solve X, not Y.
    1. The problem is X. The proposed solution is Y.
    2. If Y is leading you down a convoluted path, it might not be the best solution.
    3. **Key Takeaway:** Listen to feedback, make sure you understand the requirements, and try not to make assumptions.
4. Provide the minimum viable code.
    1. "Minimum" does not mean "bad."
    2. Simple code that achieves the desired result is good code. It's easy for others to understand and debug.
    3. **Key Takeaway:** Don't over-engineer a solution. Focus instead on creating code that is extensible and easy to build upon.
5. Create solutions that reduce complexity.
    1. Nobody wants to add yet another tool to their network. They already have too many.
    2. If it is necessary to add an extra tool like Net-Manage, then it should result in a net reduction in complexity.
    3. It does not have to replace other tools, but it does need to make them easier to leverage.
    4. **Key Takeaway:** Don't recreate the wheel. Focus on solving problems that are missing in other tools.
6. Write functional code.
    1. If you don't know the difference between functional and object-oriented programming, this article explains it well: https://www.educative.io/blog/functional-programming-vs-oop
    2. Both methodologies have their place. Which one is best depends on the use case.
    3. I chose a functional approach because functional code is easier to debug and unit test--two things that are critical when automating management of infrastructure.
    4. Many of the libraries that Net-Manage relies on (like Pandas) are OOP libaries. Neither way is inherently better or worse.
    5. **Key Takeaway:** Use the right process for the right problem. In this case, that means using functional programming.

## Platform Support

Net-Manage is designed and tested for usage on Ubuntu 20.04 with Python 3.8-3.10. However, it has been known to work on other platforms such as MacOS and Windows (using the Windows Subsystem for Linux), but please note that these are not officially supported platforms. For any issues encountered during installation or usage on unsupported platforms, we will not be able to provide any official support.

## Contact

For further queries, please raise an issue on the repository.
