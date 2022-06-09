# chain     :: pem <= []crt
# dhparam   :: pem <= int (#bits)
# gen-ca    :: crt <= conf, key
# gen-csr   :: csr <= conf, key
# gen-key    :: key <= int (#bits)
# gen-ecckey :: key <= string (ECC Prime)
# self-sign :: crt <= days, hash, extensions, conf, csr, key (self)
# sign      :: crt <= days, hash, extensions, conf, csr, key (CA), crt (CA)

# Note: Files and paths must not contain spaces.

DOMAIN = localhost
DEFAULT_CERT_TYPE = rsa2048
DEFAULT_DAYS = 730
DEFAULT_HASH = sha256
DEST = gen/

DEFAULT_CA_SIGN = 3650 $(DEFAULT_HASH) req_v3_ca
DEFAULT_server_SIGN = $(DEFAULT_DAYS) $(DEFAULT_HASH) req_v3_usr

.PHONY: all
all: install

.PHONY: clean
clean:
	rm -rf $(DEST)

# root CA #############################
$(DEST)ca-root.key:
	./tool gen-key $@ $(DOMAIN) 4096
$(DEST)ca-root.crt: conf/ca-root.conf $(DEST)ca-root.key
	./tool gen-ca $@ $(DOMAIN) $^

# intermediate CA #####################
$(DEST)ca-intermediate.key:
	./tool gen-key $@ $(DOMAIN) 4096
$(DEST)ca-intermediate.csr: conf/ca-intermediate.conf $(DEST)ca-intermediate.key
	./tool gen-csr $@ $(DOMAIN) $^
$(DEST)ca-intermediate.crt: conf/ca-intermediate.conf $(DEST)ca-intermediate.csr $(DEST)ca-root.key $(DEST)ca-root.crt
	./tool sign $@ $(DOMAIN) $(DEFAULT_CA_SIGN) $^

# server cert #########################
$(DEST)server-rsa2048.key:
	./tool gen-key $@ $(DOMAIN) 2048
$(DEST)server-rsa2048.csr: conf/server.conf $(DEST)server-rsa2048.key
	./tool gen-csr $@ $(DOMAIN) $^
$(DEST)server-rsa2048.crt: conf/server.conf $(DEST)server-rsa2048.csr $(DEST)ca-intermediate.key $(DEST)ca-intermediate.crt
	./tool sign $@ $(DOMAIN) $(DEFAULT_server_SIGN) $^
$(DEST)server-rsa2048.pem: $(DEST)server-rsa2048.crt $(DEST)ca-intermediate.crt
	./tool chain $@ $(DOMAIN) $^
CHAINS += $(DEST)server-rsa2048.pem

# client root CA ######################
$(DEST)client-ca-root.key:
	./tool gen-key $@ $(DOMAIN) 4096
$(DEST)client-ca-root.crt: conf/client-ca-root.conf $(DEST)client-ca-root.key
	./tool gen-ca $@ $(DOMAIN) $^

# client cert #########################
$(DEST)client.key:
	./tool gen-key $@ $(DOMAIN) 2048
$(DEST)client.csr: conf/client.conf $(DEST)client.key
	./tool gen-csr $@ $(DOMAIN) $^
$(DEST)client.crt: conf/client.conf $(DEST)client.csr $(DEST)client-ca-root.key $(DEST)client-ca-root.crt
	./tool sign $@ $(DOMAIN) $(DEFAULT_server_SIGN) $^
$(DEST)client.p12: $(DEST)client.crt $(DEST)client.key
	./tool gen-pkcs12-p12 $@ $(DOMAIN) $^
$(DEST)client.pem: $(DEST)client.p12
	./tool pkcs12-convert-p12-pem $@ $(DOMAIN) $^
CHAINS += $(DEST)client.pem

#######################################

.PHONY: chains
chains: $(CHAINS)

.PHONY: install
install: $(CHAINS)
	cp $(DEST)client.key ../client.key
	cp $(DEST)client.crt ../client.crt
	cp $(DEST)client-ca-root.crt ../client-ca-root.crt
	cp $(DEST)server-rsa2048.key ../server.key
	cp $(DEST)server-rsa2048.pem ../server_chain.pem
	cp $(DEST)ca-root.crt ../ca-root.crt

