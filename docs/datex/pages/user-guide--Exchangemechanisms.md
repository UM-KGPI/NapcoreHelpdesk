url: https://docs.datex2.eu/v3.7/user-guide/Exchangemechanisms/
title: Exchange mechanisms

## Exchange mechanisms
Generally speaking, DATEX II offers a push and a pull mode for information exchange. The push mode (as in DATEX) allows the supplier to send information to the client while the pull mode allows the client to request the download of information from the supplier’s systems. In detail, DATEX II provides the exchange mechanisms as described below. At a high description level document for details, without considering the notion of technical platforms, data exchange between a supplier and its client(s) can be accomplished by three main operating modes:
- Operating Mode 1 - Publisher Push on occurrence
- data delivery initiated by the publisher every time data is changed
- Operating Mode 2 - Publisher Push periodic
- data delivery initiated by the publisher on a cyclic time basis
- Operating Mode 3 - Client Pull
- data delivery initiated by the Client, where data is returned as a response.
Each Operating Mode can be both on- and offline. For the "Client Pull" operating mode, two implementation profiles have been defined for implementing this operating mode over the Internet: by direct use of the HTTP/1.1 protocol or via Web Services over HTTP. For the "Supplier Push" operating modes, one platform has been defined using Web Services over HTTP. The common corresponding document, describing all operating modes and both profiles for Client Pull as well as their interoperability, is [Exchange PSM]. PSM exchange documents have been designed to be independent from the exchanged content (the payload). These documents can be studied without knowing the details of the UML DATEX II data model.
Go back to the previous page
