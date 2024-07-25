import argparse
import ast
import os
import pandas as pd
import requests
from datetime import datetime
from netmanage.helpers import cisco_aci_helpers as cah
from netmanage.helpers import helpers as hp
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from typing import Any, Dict, Optional


class AppConfig:
    """
    A class to provide access to the application's configuration settings.
    """

    pass


def load_environment_variables(env_path: str) -> AppConfig:
    """
    Loads environment variables from a specified file.

    Parameters
    ----------
    env_path : str
        The full path to the environment file.

    Returns
    -------
    config : AppConfig
        An instance of AppConfig containing the deployment variables.
    """
    logger = hp.setup_logger()
    config = AppConfig()
    env_path = os.path.expanduser(env_path)

    def validate_env_path(path: str):
        if not os.path.exists(path):
            failure_msg = f"Error: could not find '{path}'. Does it exist?"
            logger.critical(failure_msg)
            raise Exception(failure_msg)
        load_dotenv(override=True, dotenv_path=path)

    def create_jobs_timestamp(cfg):
        now = datetime.now()
        setattr(cfg, "timestamp", now.strftime("%Y-%m-%d %H:%M:%S.%f"))

    def get_path_variables(cfg):
        path_vars = {
            "db_path": os.path.join(
                hp.get_expanded_path("database_path"),
                hp.get_expanded_path("database_name"),
            ),
            "divergence_path": hp.get_expanded_path("divergence_path"),
            "logs_db": hp.get_expanded_path("logs_db"),
            "utils_db": hp.get_expanded_path("utils_db"),
            "artifacts_path": hp.get_expanded_path("artifacts_path"),
        }
        missing_vars = [key for key, value in path_vars.items() if not value]
        for key, value in path_vars.items():
            setattr(cfg, key, value)
        if missing_vars:
            for var in missing_vars:
                logger.warning(f"Missing environment variable: {var}")

    def get_aci_variables(cfg):
        sites = os.environ.get("aci_sites")
        if sites:
            sites = hp.remove_duplicates(hp.strip_list_spaces(sites.split(",")))
            aci_sites = {site: {} for site in sites}
            for site in sites:
                fixed_site = site.replace(" ", "-")
                aci_sites[site] = {
                    "site_name": site,
                    "apic_urls": process_urls(
                        os.environ.get(f"aci_sites_{fixed_site}_apic_urls")
                    ),
                    "username": os.environ.get(f"aci_sites_{fixed_site}_username"),
                    "password": os.environ.get(f"aci_sites_{fixed_site}_password"),
                }
                check_credentials(aci_sites[site], site)
            setattr(cfg, "aci_sites", aci_sites)

    def process_urls(urls: str):
        if urls:
            urls = hp.remove_duplicates(hp.strip_list_spaces(urls.split(",")))
            return [
                "https://" + url if not url.startswith("https://") else url
                for url in urls
            ]
        return []

    def check_credentials(site_info, site_name):
        if not site_info["username"]:
            logger.warning(f"The username for site '{site_name}' is blank.")
        if not site_info["password"]:
            logger.warning(f"The password for site '{site_name}' is blank.")

    def set_cert_validation_boolean(cfg):
        setattr(cfg, "validate_certs", ast.literal_eval(os.environ["validate_certs"]))

    validate_env_path(env_path)
    create_jobs_timestamp(config)
    get_path_variables(config)
    get_aci_variables(config)
    set_cert_validation_boolean(config)

    return config


def get_nodes_attributes(
    url: str, token: str, verify: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Retrieve node attributes from an ACI APIC.

    Parameters
    ----------
    url : str
        The base URL of the ACI APIC to which the request is sent.
    token : str
        The authentication token used for the APIC session.
    verify : bool, optional
        A boolean indicating whether to verify the server's TLS certificate.
        Defaults to True.

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing the response data with node attributes, or None if
        an error occurs during the request.

    Raises
    ------
    HTTPError
        If the HTTP request returned an unsuccessful status code.
    Exception
        If any other exception occurred during the request.
    """
    return make_aci_request(f"{url}/api/node/class/topSystem.json", token, verify)


def get_site_subnets(
    url: str, token: str, verify: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Retrieve site subnets from an ACI APIC.

    Parameters
    ----------
    url : str
        The base URL of the ACI APIC to which the request is sent.
    token : str
        The authentication token used for the APIC session.
    verify : bool, optional
        A boolean indicating whether to verify the server's TLS certificate.
        Defaults to True.

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing the response data with site subnets, or None if
        an error occurs during the request.

    Raises
    ------
    HTTPError
        If the HTTP request returned an unsuccessful status code.
    Exception
        If any other exception occurred during the request.
    """
    df = make_aci_request(f"{url}/api/node/class/fvSubnet.json", token, verify)
    if not df.empty:
        df[["address", "cidr"]] = df["ip"].str.split("/", expand=True)
        df["network_ip"] = df["ip"].apply(get_network_ip)
    return df


def get_network_ip(ip_with_cidr):
    """
    Calculate the network IP from an IP address with CIDR notation.

    Parameters
    ----------
    ip_with_cidr : str
        IP address with CIDR notation.

    Returns
    -------
    str
        Network IP address.
    """
    import ipaddress

    network = ipaddress.ip_network(ip_with_cidr, strict=False)
    return str(network.network_address)


def get_site_inventory(
    url: str, token: str, verify: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Retrieve site inventory from an ACI APIC.

    Parameters
    ----------
    url : str
        The base URL of the ACI APIC to which the request is sent.
    token : str
        The authentication token used for the APIC session.
    verify : bool, optional
        A boolean indicating whether to verify the server's TLS certificate.
        Defaults to True.

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing the response data with site inventory, or None if
        an error occurs during the request.

    Raises
    ------
    HTTPError
        If the HTTP request returned an unsuccessful status code.
    Exception
        If any other exception occurred during the request.
    """
    return make_aci_request(f"{url}/api/node/class/fabricNode.json", token, verify)


def get_site_client_endpoint_ips(
    url: str, token: str, verify: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Retrieve site endpoints from an ACI APIC.

    Parameters
    ----------
    url : str
        The base URL of the ACI APIC to which the request is sent.
    token : str
        The authentication token used for the APIC session.
    verify : bool, optional
        A boolean indicating whether to verify the server's TLS certificate.
        Defaults to True.

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing the response data with site endpoints, or None if
        an error occurs during the request.

    Raises
    ------
    HTTPError
        If the HTTP request returned an unsuccessful status code.
    Exception
        If any other exception occurred during the request.
    """
    return make_aci_request(
        f"{url}/api/node/class/fvIp.json?rsp-subtree=full", token, verify
    )


def get_site_bridge_domains(
    url: str, token: str, verify: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Retrieve site bridge domains from an ACI APIC.

    Parameters
    ----------
    url : str
        The base URL of the ACI APIC to which the request is sent.
    token : str
        The authentication token used for the APIC session.
    verify : bool, optional
        A boolean indicating whether to verify the server's TLS certificate.
        Defaults to True.

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing the response data with site bridge domains, or None if
        an error occurs during the request.

    Raises
    ------
    HTTPError
        If the HTTP request returned an unsuccessful status code.
    Exception
        If any other exception occurred during the request.
    """
    return make_aci_request(f"{url}/api/node/class/fvBD.json", token, verify)


def make_aci_request(url: str, token: str, verify: bool) -> Optional[pd.DataFrame]:
    """
    Helper function to make an HTTP GET request to the ACI APIC and process the response.

    Parameters
    ----------
    url : str
        The URL for the ACI APIC API endpoint.
    token : str
        The authentication token for the APIC session.
    verify : bool
        Whether to verify the server's TLS certificate.

    Returns
    -------
    Optional[pd.DataFrame]
        A DataFrame containing the response data, or None if an error occurs during the request.
    """
    logger = hp.setup_logger()
    headers = {"Cookie": f"APIC-cookie={token}"}
    try:
        response = requests.get(url, headers=headers, verify=verify)
        response.raise_for_status()
        attributes = response.json()
        flattened_data = [
            item[next(iter(item))]["attributes"] for item in attributes["imdata"]
        ]
        return pd.DataFrame(flattened_data)
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logger.error(f"An error occurred: {err}")
    return pd.DataFrame()


def save_collector(
    logger, config, site, params, collector_func, db_table, excluded_columns
):
    """
    Collects data from ACI site using the specified collector function and stores it in the database.

    Args:
        logger (logging.Logger): Logger instance for logging messages.
        config (AppConfig): Configuration object containing ACI site details and database path.
        site (str): Name of the ACI site.
        params (dict): Dictionary containing site parameters including APIC URLs and tokens.
        collector_func (function): Function to collect data from the ACI site.
        db_table (str): Name of the database table to store the collected data.
        excluded_columns (list): List of columns to exclude from the database index.

    Returns:
        None
    """
    token = params.get("token")
    if token:
        for url in params["apic_urls"]:
            msg = f"Collecting data from site '{site}' url: '{url}' using {collector_func.__name__}"
            logger.info(msg)
            df = collector_func(url, token, verify=config.validate_certs)
            df.insert(len(df.columns), "site", site)
            if not df.empty:
                config.aci_sites[site]["apic_urls"] = hp.move_list_element_to_front(
                    config.aci_sites[site]["apic_urls"], url
                )
                break
        if not df.empty:
            id_cols = [_ for _ in df.columns.to_list() if _ not in excluded_columns]
            logger.info(f"site: {site}, records: {df.shape}")
            cah.store_results_in_db(
                df, config.db_path, db_table, config.timestamp, id_cols
            )


def main(env_path: str):
    """
    Main function to set up the logger, load environment variables, authenticate to ACI sites,
    and collect various types of data from the sites.

    Args:
        env_path (str): Path to the environment variables file.

    Returns:
        None
    """
    logger = hp.setup_logger()
    config = load_environment_variables(env_path)

    for site, params in config.aci_sites.items():
        for url in params["apic_urls"]:
            logger.info(f"Getting auth token for site: {site}, url: {url}")
            token = cah.get_auth_token(
                url,
                params["username"],
                params["password"],
                verify=config.validate_certs,
            )
            if isinstance(token, str):
                config.aci_sites[site]["token"] = token
                config.aci_sites[site]["apic_urls"] = hp.move_list_element_to_front(
                    config.aci_sites[site]["apic_urls"], url
                )
                break

    collectors = [
        (
            get_site_bridge_domains,
            "CISCO_ACI_GET_SITE_bridge_domains",
            ["modTs", "lastStateModTs"],
        ),
        (
            get_site_inventory,
            "CISCO_ACI_GET_SITE_fabric_nodes",
            ["modTs", "lastStateModTs"],
        ),
        (
            get_site_client_endpoint_ips,
            "CISCO_ACI_GET_SITE_client_endpoint_ips",
            ["modTs"],
        ),
        (
            get_nodes_attributes,
            "CISCO_ACI_GET_NODES_ATTRIBUTES",
            ["clusterTimeDiff", "currentTime", "modTs", "systemUpTime"],
        ),
        (get_site_subnets, "CISCO_ACI_GET_SITE_SUBNETS", ["modTs"]),
    ]

    for collector, db_table, excluded_columns in collectors:
        for site, params in config.aci_sites.items():
            save_collector(
                logger, config, site, params, collector, db_table, excluded_columns
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run data collection on Cisco ACI Fabrics."
    )
    parser.add_argument(
        "-e",
        "--env_path",
        required=True,
        help="Full path to the file containing environment variables.",
    )
    args = parser.parse_args()
    main(args.env_path)
