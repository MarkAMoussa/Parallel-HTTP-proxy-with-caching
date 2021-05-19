# Don't forget to change this file's name before submission.
import sys
import os
import enum
import socket
import _thread


# done
class HttpRequestInfo(object):
    """
    Represents a HTTP request information
    Since you'll need to standardize all requests you get
    as specified by the document, after you parse the
    request from the TCP packet put the information you
    get in this object.
    To send the request to the remote server, call to_http_string
    on this object, convert that string to bytes then send it in
    the socket.
    client_address_info: address of the client;
    the client of the proxy, which sent the HTTP request.
    requested_host: the requested website, the remote website
    we want to visit.
    requested_port: port of the webserver we want to visit.
    requested_path: path of the requested resource, without
    including the website name.
    NOTE: you need to implement to_http_string() for this class.
    """

    # leave as is
    def __init__(self, client_info, method: str, requested_host: str,
                 requested_port: int,
                 requested_path: str,
                 headers: list):
        self.method = method
        self.client_address_info = client_info
        self.requested_host = requested_host
        self.requested_port = requested_port
        self.requested_path = requested_path
        # Headers will be represented as a list of lists
        # for example ["Host", "www.google.com"]
        # if you get a header as:
        # "Host: www.google.com:80"
        # convert it to ["Host", "www.google.com"] note that the
        # port is removed (because it goes into the request_port variable)
        self.headers = headers

    # done
    def to_http_string(self):
        """
        Convert the HTTP request/response
        to a valid HTTP string.
        As the protocol specifies:
        [request_line]\r\n
        [header]\r\n
        [headers..]\r\n
        \r\n
        (just join the already existing fields by \r\n)
        You still need to convert this string
        to byte array before sending it to the socket,
        keeping it as a string in this stage is to ease
        debugging and testing.
        """
        http_version = "HTTP/1.0"
        http_string = self.method + " " + self.requested_path + " " + http_version + "\r\n"
        length = 0
        while length < len(self.headers):
            http_string += self.headers[length][0] + ": "
            if(self.headers[length][1]):
                http_string += self.headers[length][1]
            http_string += "\r\n"
            length += 1
        http_string += "\r\n"
        return http_string

    # leave as is
    def to_byte_array(self, http_string):
        """
        Converts an HTTP string to a byte array.
        """
        return bytes(http_string, "UTF-8")

    # leave as is
    def display(self):
        print(f"Client:", self.client_address_info)
        print(f"Method:", self.method)
        print(f"Host:", self.requested_host)
        print(f"Port:", self.requested_port)
        stringified = [": ".join([k, v]) for (k, v) in self.headers]
        print("Headers:\n", "\n".join(stringified))


# done
class HttpErrorResponse(object):
    """
    Represents a proxy-error-response.
    """

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def to_http_string(self):
        """ Same as above """
        http_version = "HTTP/1.0"
        error_string = http_version + " " + \
            str(self.code) + " " + self.message + "\r\n\r\n"
        return error_string

    def to_byte_array(self, http_string):
        """
        Converts an HTTP string to a byte array.
        """
        return bytes(http_string, "UTF-8")

    def display(self):
        print(self.to_http_string())


# leave as is
class HttpRequestState(enum.Enum):
    """
    The values here have nothing to do with
    response values i.e. 400, 502, ..etc.
    Leave this as is, feel free to add yours.
    """
    INVALID_INPUT = 0
    NOT_SUPPORTED = 1
    GOOD = 2
    PLACEHOLDER = -1


# done
def entry_point(proxy_port_number):
    """
    Entry point, start your code here.
    Please don't delete this function,
    but feel free to modify the code
    inside it.
    """
    # creating a proxy socket
    sock_client_proxy = setup_sockets(proxy_port_number)
    # creating a common cache
    cache = dict()

    # creating 20 threads for 20 clients
    for i in range(0, 20):
        try:
            _thread.start_new_thread(
                do_socket_logic, (sock_client_proxy, cache))
        except:
            print("no thread bibi")

    # to not kill the parent
    while True:
        pass


# a5iran done
def do_socket_logic(sock_client_proxy, cache):

    # main loop
    while True:

        # creating server socket
        sock_proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # accepting a client request
        client_sock, client_address = sock_client_proxy.accept()
        # taking in 1024 packets from the user
        data = client_sock.recv(1024)
        # decode the client's request
        byte_data = data.decode("utf-8")
        # after the request being parsed and validated we return different types
        request = http_request_pipeline(client_address, byte_data)

        # if the returned value of the request is HttpErrorResponse
        if isinstance(request, HttpErrorResponse):
            # we turn it into string then a byte array
            request = request.to_byte_array(request.to_http_string())
            # send the request and then close the socket
            client_sock.send(request)
            client_sock.close()
            # we are done with this iteration
            continue
        # if it's a normal request
        elif isinstance(request, HttpRequestInfo):
            # we ask if it's in the cache
            if request.requested_host + request.requested_path in cache:
                # we send the data from the cache to the client using the host and path as key for the dictionary
                client_sock.send(
                    cache[request.requested_host + request.requested_path])
                # we close the socket
                client_sock.close()
                # we are done with this iteration
                continue
            # we do as we did in the case of error
            request_byte = request.to_byte_array(request.to_http_string())
            # but we establish a connection with server first
            sock_proxy_server.connect(
                (request.requested_host, int(request.requested_port)))
            # then send the request to the server
            sock_proxy_server.send(request_byte)
            # we create an entry in the cache using the key mentioned above
            cache[request.requested_host + request.requested_path] = b""
            while True:
                # we recive the data from the server
                recieved_data = sock_proxy_server.recv(1024)
                # then save it into the cache
                cache[request.requested_host +
                      request.requested_path] += recieved_data
                # then send it to the client
                client_sock.send(recieved_data)
                # the condition of stopping and ending this iteration
                if len(recieved_data) <= 0:
                    # close the client socket
                    client_sock.close()
                    # close the server socket
                    sock_proxy_server.close()
                    # end of iteration
                    break


# done
def setup_sockets(proxy_port_number):
    """
    Socket logic MUST NOT be written in the any
    class. Classes know nothing about the sockets.
    But feel free to add your own classes/functions.
    Feel free to delete this function.
    """
    print("Starting HTTP proxy on port:", proxy_port_number)

    # when calling socket.listen() pass a number
    # that's larger than 10 to avoid rejecting
    # connections automatically.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", proxy_port_number))
    # sets the number to listeners
    sock.listen(20)
    return sock


# done
def http_request_pipeline(source_addr, http_raw_data):
    """
    HTTP request processing pipeline.
    - Validates the given HTTP request and returns
      an error if an invalid request was given.
    - Parses it
    - Returns a sanitized HttpRequestInfo
    returns:
     HttpRequestInfo if the request was parsed correctly.
     HttpErrorResponse if the request was invalid.
    Please don't remove this function, but feel
    free to change its content
    """
    validity = check_http_request_validity(http_raw_data)

    # in case of error we create an error response and assign it's appropriate values
    if validity == HttpRequestState.INVALID_INPUT:

        error_response = HttpErrorResponse(400, "Bad Request")
        return error_response

    elif validity == HttpRequestState.NOT_SUPPORTED:
        error_response = HttpErrorResponse(501, "Not Implemented")
        return error_response
    # in case of no error we create a proper html request and parse it getting it's values
    http_request = parse_http_request(source_addr, http_raw_data)
    return http_request


# parsing http requests
def parse_http_request(source_addr, http_raw_data):
    """
    This function parses a "valid" HTTP request into an HttpRequestInfo
    object.
    """
    temp_data = http_raw_data.replace("\r\n", " ").strip()

    temp_data = temp_data.split()
    # method is always the first element in the request
    method = temp_data[0]

    # if it's direct request the method is always followed by /
    if temp_data[1][0] == "/":
        # we get the path
        path = temp_data[1]
        # we split in stead of replace
        temp_data[4] = temp_data[4].split(":")
        # assign the host
        host = temp_data[4][0]
        # get the port if it exists
        if len(temp_data[4]) == 2:
            port = temp_data[4][1]
        # if not give it 80 as default
        else:
            port = str(80)
        # get the headers
        headers = [[temp_data[3][0:-1], temp_data[4][0]]]
        length = 5
        while length < len(temp_data):
            headers.append([temp_data[length][0:-1], temp_data[length+1]])
            length += 2
    # if it's not direct request
    else:
        # trim the http part
        my_string = temp_data[1].replace("http://", "")
        # split using /
        my_string = my_string.split("/")
        path = ""
        # getting the path
        for i in range(1, len(my_string)):
            path += "/" + my_string[i]

        # checking for port and host
        if ":" in my_string[0]:
            my_string[0] = my_string[0].split(":")
            host = my_string[0][0]
            port = my_string[0][1]
        else:
            host = my_string[0]
            port = str(80)

        headers = []
        length = 3
        # getting the headers
        while length < len(temp_data):
            headers.append([temp_data[length][0:-1]])
            length += 1
            if length < len(temp_data):
                headers[-1].append(temp_data[length])
            else:
                headers[-1].append("")
            length += 1
    # creating a proper http request object
    ret = HttpRequestInfo(source_addr, method, host, port, path, headers)
    return ret


# done
def check_http_request_validity(http_raw_data):
    """
    Checks if an HTTP request is valid
    returns:
    One of values in HttpRequestState
    """
    # not supported requests list
    not_supported_requests = ["HEAD", "POST", "DELETE",
                              "CONNECT", "PATCH", "TRACE", "OPTIONS", "PUT"]
    # all http versions
    http_versions = ["HTTP/0.9", "HTTP/1.0", "HTTP/1.1", "HTTP/2.0"]

    # we strip and replace as above
    temp_data = http_raw_data.replace("\r\n", " ").strip()
    temp_data = temp_data.split()

    # check for the type of request and if the host header exist
    if temp_data[1][0] == "/" and not "Host:" in http_raw_data:
        return HttpRequestState.INVALID_INPUT

    # check for the http version
    if not temp_data[2] in http_versions:
        return HttpRequestState.INVALID_INPUT

    if len(temp_data) > 3:
        if not temp_data[3][-1] == ":":
            return HttpRequestState.INVALID_INPUT
        elif not len(temp_data) > 4:
            return HttpRequestState.INVALID_INPUT

    if temp_data[0] == "GET":
        return HttpRequestState.GOOD
    elif temp_data[0] in not_supported_requests:
        return HttpRequestState.NOT_SUPPORTED
    else:
        return HttpRequestState.INVALID_INPUT


#######################################
# Leave the code below as is.
#######################################


def get_arg(param_index, default=None):
    """
        Gets a command line argument by index (note: index starts from 1)
        If the argument is not supplies, it tries to use a default value.
        If a default value isn't supplied, an error message is printed
        and terminates the program.
    """
    try:
        return sys.argv[param_index]
    except IndexError as e:
        if default:
            return default
        else:
            print(e)
            print(
                f"[FATAL] The comand-line argument #[{param_index}] is missing")
            exit(-1)    # Program execution failed.


def check_file_name():
    """
    Checks if this file has a valid name for *submission*
    leave this function and as and don't use it. it's just
    to notify you if you're submitting a file with a correct
    name.
    """
    script_name = os.path.basename(__file__)
    import re
    matches = re.findall(r"(\d{4}_){,2}lab2\.py", script_name)
    if not matches:
        print(f"[WARN] File name is invalid [{script_name}]")
    else:
        print(f"[LOG] File name is correct.")


def main():
    """
    Please leave the code in this function as is.
    To add code that uses sockets, feel free to add functions
    above main and outside the classes.
    """
    print("\n\n")
    print("*" * 50)
    print(f"[LOG] Printing command line arguments [{', '.join(sys.argv)}]")
    check_file_name()
    print("*" * 50)

    # This argument is optional, defaults to 18888
    proxy_port_number = get_arg(1, 18888)
    entry_point(proxy_port_number)


if __name__ == "__main__":
    main()
