"""Python library to interact with the Gumroad API.

https://gumroad.com/api

Note that not all endpoints and HTTP verbs have been added.

Usage:

import pygumroad
gumroad_client = pygumroad.GumroadClient(secrets_file_location="/home/user/secrets.json")
all_products = gumroad_client.retrieve_all_products()
"""

# Standard Python libraries.
import json
import random
import string
import sys
# import urllib3

# Third party Python libraries.
import requests
from requests_toolbelt.utils import dump

# Custom Python libraries.


__version__ = "0.0.1"


class GumroadClient:
    def __init__(self, secrets_dict={}, secrets_file_location="./gumroad_secrets.json", **kwargs):
        """Initialize a Gumroad client.  The secrets dict should look like:

            secrets_dict = {
                "gumroad": {
                    "host": host,
                    "token": token,
                }
            }
        """

        if secrets_dict:
            secrets = secrets_dict

        elif secrets_file_location:
            try:
                with open(secrets_file_location) as config_file:
                    secrets = json.loads(config_file.read())
            except OSError:
                print(f"Error: {secrets_file_location} does not exist.  Exiting...")
                sys.exit(1)

        else:
            print(
                "Error initializing a GumroadClient client.  Provide a secrets dictionary or secrets file "
                "location.  Exiting..."
            )
            sys.exit(1)

        # Ensure key/values exist in secrets.
        try:
            self.host = secrets["gumroad"]["host"]
            self.token = secrets["gumroad"]["token"]

        except KeyError:
            print(f"Error reading key-values in 'secrets' variable.  Exiting...")
            sys.exit(1)

        # Build BASE_URL.
        self.BASE_URL = f"https://{self.host}"

        # Minimize Python requests (and the underlying urllib3 library) logging level.
        # logging.getLogger("requests").setLevel(logging.INFO)
        # logging.getLogger("urllib3").setLevel(logging.INFO)

        # Extract User-Agent, default to "gumroad-api-client-v(version)".
        self.user_agent = kwargs.get("user_agent", f"pygumroad-api-client-v{__version__}")

        self.headers = {"User-Agent": self.user_agent}

        self.payload = {"access_token": self.token}

        # Extract timeout, default to 30 seconds.
        self.timeout = kwargs.get("timeout", 30)

        # Extract max attempts, default to 3.
        self.max_attempts = kwargs.get("max_attempts", 3)

        # Max is 10, set on the server side.
        self.max_results_returned_from_api = kwargs.get("max_results_returned_from_api", 10)

        self.base_path = "/v2"

        # Extract api_self_signed, defaults to False.
        self.api_self_signed = kwargs.get("api_self_signed", False)

        # if self.api_self_signed:
        #     urllib3.disable_warnings()

        self.debug_print = False

    def api_query(self, endpoint, **kwargs):
        """Executes a properly formatted API call to the Gumroad API with the supplied arguments."""

        url = f"{self.BASE_URL}{endpoint}"

        # Set HTTP headers.
        headers = kwargs.get("headers", {})

        if not isinstance(headers, dict):
            raise ValueError("headers keyword passed to api_query is not a valid dict object")

        # Merge dictionaries.
        # https://treyhunner.com/2016/02/how-to-merge-dictionaries-in-python/
        headers = {**self.headers, **headers}

        # Extract HTTP verb, defaults to GET.
        method = kwargs.get("method", "GET")
        method = method.upper()

        # Extract additional parameters, defaults to an empty dictionary.
        parameters = kwargs.get("parameters", {})

        if not isinstance(parameters, dict):
            raise ValueError("parameters keyword passed to api_query is not a valid dict object")

        # Extract payload.
        payload = kwargs.get("payload", {})
        payload = {**self.payload, **payload}

        # Used to track number of failed HTTP requests.
        attempts = 0

        while True:
            try:
                if method == "GET":
                    response = requests.get(
                        url, headers=headers, data=payload, verify=(not self.api_self_signed), timeout=self.timeout
                    )

                    if response.status_code != 200:
                        debug_requests_response(response)

                    break

                elif method == "POST":
                    response = requests.post(
                        url, headers=headers, json=payload, verify=(not self.api_self_signed), timeout=self.timeout
                    )

                    # Normally it's an HTTP 201, but retrieve_api_token_from_username_and_password() function can return
                    # a 200 response even when sending a POST.
                    if response.status_code not in [200, 201]:
                        debug_requests_response(response)

                    break

                elif method == "PUT":
                    response = requests.put(
                        url, headers=headers, json=payload, verify=(not self.api_self_signed), timeout=self.timeout
                    )

                    if response.status_code != 200:
                        debug_requests_response(response)

                    break

                elif method == "DELETE":
                    response = requests.delete(
                        url, headers=headers, json=payload, verify=(not self.api_self_signed), timeout=self.timeout
                    )

                    if response.status_code != 204:
                        debug_requests_response(response)

                    break

                else:
                    print(f"Invalid HTTP method passed to api_query: {method}")
                    raise ValueError(f"Invalid HTTP method passed to api_query: {method}")

            except (
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
            ):
                attempts += 1
                if self.max_attempts < attempts:
                    print(
                        f"Unable to reach Gumroad API after {self.max_attempts} tries.  Consider increasing the "
                        "timeout."
                    )
                    sys.exit(1)
                else:
                    print("Packet loss when attempting to reach the Gumroad API.")

        if self.debug_print:
            debug_requests_response(response)

        return response

    # PRODUCTS
    def retrieve_all_products(self):
        """Retrieve all the products"""

        response = self.api_query("/v2/products", method="GET")
        json_response = response.json()

        all_product_info = None

        if json_response["success"] is True:
            all_product_info = json_response["products"]
        else:
            print("Unable to retrieve all product info.")

        return all_product_info

    def retrieve_product_info(self, product_id):
        """Retrieve the product information given a product_id"""

        response = self.api_query(f"/v2/products/{product_id}", method="GET")
        json_response = response.json()

        product_info = None

        if json_response["success"] is True:
            product_info = json_response["product"]
        else:
            print("Unable to retrieve all product info.")

        return product_info

    # OFFERCODES
    def retrieve_offer_codes_for_product(self, product_id):
        """Retrieve the offer codes given a product_id"""

        response = self.api_query(f"/v2/products/{product_id}/offer_codes", method="GET")
        json_response = response.json()

        offer_codes = []

        if json_response["success"] is True:
            offer_codes = json_response["offer_codes"]
        else:
            print(f"Unable to retrieve all offer codes for product ID: {product_id}")

        return offer_codes

    def retrieve_offer_code_details_for_product(self, product_id, offer_code_id):
        """Retrieve the offer codes given a product_id and offer_code_id"""

        response = self.api_query(f"/v2/products/{product_id}/offer_codes/{offer_code_id}", method="GET")
        json_response = response.json()

        offer_code = None

        if json_response["success"] is True:
            offer_code = json_response["offer_code"]
        else:
            print("Unable to retrieve the offer code.")

        return offer_code

    def create_offer_code_for_product(self, product_id, payload={}):
        """Create an offer code for a product"""

        response = self.api_query(f"/v2/products/{product_id}/offer_codes", method="POST", payload=payload)
        json_response = response.json()

        offer_code = []

        if json_response["success"] is True:
            offer_code = json_response["offer_code"]
        else:
            print("Unable to create the offer code.")

        return offer_code

    # SALES
    def retrieve_sales(self, payload={}, page=1):
        """Retrieve sales given an optional payload or page."""

        payload["page"] = page

        response = self.api_query("/v2/sales", method="GET", payload=payload)
        json_response = response.json()

        sales = []

        if json_response["success"] is True:
            sales = json_response["sales"]
        else:
            print("Unable to retrieve sales.")

        return sales

    def retrieve_all_sales(self, payload={}, page=1):
        """Retrieve all the sales given an optional payload or page"""

        all_sales = []

        payload["page"] = page

        response = self.api_query(f"/v2/sales", method="GET", payload=payload)
        json_response = response.json()

        if json_response["success"] is True:
            sales = json_response["sales"]
            all_sales += sales

        # Only runs if more than 10 sales exist, since each page only pulls back 10 at a time.
        if "next_page_url" in json_response:
            next_page_url = json_response["next_page_url"]

            while next_page_url:

                # Update the page key.
                page += 1
                payload["page"] = page

                response = self.api_query(f"/v2/sales", method="GET", payload=payload)
                json_response = response.json()

                if json_response["success"] is True:
                    sales = json_response["sales"]
                    all_sales += sales

                if "next_page_url" in json_response:
                    next_page_url = json_response["next_page_url"]
                else:
                    next_page_url = None

        return all_sales

    # Custom functions.
    def retrieve_all_offer_code_names_for_a_product(self, product_id):
        """Given a product ID, retrieve all the offer codes and return them in a list."""

        offer_codes = self.retrieve_offer_codes_for_product(product_id)

        current_offer_codes = []

        for offer_code in offer_codes:
            current_offer_codes.append(offer_code["name"])

        return current_offer_codes

    def generate_new_offer_code_for_a_product(self, product_id, offer_code_length=32, current_offer_codes=[]):
        """Generate a random offer_code_length character offer code given a product ID."""

        if not current_offer_codes:
            current_offer_codes = self.retrieve_all_offer_code_names_for_a_product(product_id)

        new_offer_code_name = None

        if current_offer_codes:
            new_offer_code_name = "".join(
                random.choice(string.ascii_lowercase + string.digits) for _ in range(offer_code_length)
            )

            # Only enters this loop if new_offer_code_name already exists.
            while new_offer_code_name in current_offer_codes:
                print(f"Offer code already exists: {new_offer_code_name}")
                new_offer_code_name = "".join(
                    random.choice(string.ascii_lowercase + string.digits) for _ in range(offer_code_length)
                )

            print(f"Generated new offer code: {new_offer_code_name}")

        return new_offer_code_name


def debug_requests_response(response):
    """Provide debug print info for a requests response object."""

    data = dump.dump_all(response)
    print(data.decode("utf-8"))


def http_status_code(http_code):
    """Contains a database of all known HTTP status codes and their corresponding plain text description.  For use in
    both program output as well as parsing for specific issue types.

    Args:
        http_code (int): A number containing the HTTP status code to lookup

    Returns:
        string: Returns a description of the status code.
    """

    http_codes = {
        200: "OK",
        201: "OK: Created",
        202: "OK: Accepted",
        203: "OK: Non-Authoritative Information",
        204: "OK: No Content",
        205: "OK: Reset Content",
        206: "OK: Partial Content",
        207: "OK: Multi-Status",
        208: "OK: Already Reported",
        226: "OK: IM Used",
        300: "Redirected: Multiple Choices",
        301: "Redirected: Moved Permanently",
        302: "Redirected: Found",
        303: "Redirected: See Other",
        304: "Redirected: Not Modified",
        305: "Redirected: Use Proxy",
        306: "Redirected: Switch Proxy",
        307: "Redirected: Temporary Redirect",
        308: "Redirected: Permanent Redirect",
        400: "Client Error: Bad Request",
        401: "Client Error: Unauthorized",
        402: "Client Error: Payment Required",
        403: "Client Error: Forbidden",
        404: "Client Error: Not Found",
        405: "Client Error: Method Not Allowed",
        406: "Client Error: Not Acceptable",
        407: "Client Error: Proxy Authentication Required",
        408: "Client Error: Request Timeout",
        409: "Client Error: Conflict",
        410: "Client Error: Gone",
        411: "Client Error: Length Required",
        412: "Client Error: Precondition Failled",
        413: "Client Error: Payload Too Large",
        414: "Client Error: URI Too Large",
        415: "Client Error: Unsupported Media Type",
        416: "Client Error: Range Not Satisfiable",
        417: "Client Error: Expectation Failed",
        418: "Client Error: I'm a teapot",
        421: "Client Error: Misdirected Request",
        422: "Client Error: Un-processable Entity",
        423: "Client Error: Locked",
        424: "Client Error: Failed Dependency",
        426: "Client Error: Upgrade Required",
        428: "Client Error: Precondition Required",
        429: "Client Error: Too Many Requests",
        431: "Client Error: Request Header Fields Too Large",
        440: "Client Error: Login Time-Out",
        444: "Client Error: No Response",
        449: "Client Error: Retry With",
        451: "Client Error: Unavailable For Legal Reasons",
        495: "Client Error: SSL Certificate Error",
        496: "Client Error: SSL Certificate Required",
        497: "Client Error: HTTP Request Sent to HTTPS Port",
        499: "Client Error: Client Closed Request",
        500: "Server Error: Internal Server Error",
        501: "Server Error: Not Implemented",
        502: "Server Error: Bad Gateway",
        503: "Server Error: Service Unavailable",
        504: "Server Error: Gateway Timeout",
        505: "Server Error: HTTP Version Not Supported",
        507: "Server Error: Insufficient Storage",
        508: "Server Error: Loop Detected",
        510: "Server Error: Not Extended",
        511: "Server Error: Network Authentication Required",
        520: "Server Error: Unknown Error when connecting to server behind load balancer",
        521: "Server Error: Web Server behind load balancer is down",
        522: "Server Error: Connection Timed Out to server behind load balancer",
        523: "Server Error: Server behind load balancer is unreachable",
        524: "Server Error: TCP handshake with server behind load balancer completed but timed out",
        525: "Server Error: Load balancer could not negotiate a SSL/TLS handshake with server behind load balancer",
        526: "Server Error: Server behind load balancer returned invalid SSL/TLS cert to load balancer",
        527: "Server Error: Load balancer request timed out/failed after WAN connection was established to origin server",
    }

    http_status = http_codes.get(http_code, "NA")

    return http_status


if __name__ == "__main__":
    print("Use 'import pygumroad', do not run directly.")
    exit(1)
