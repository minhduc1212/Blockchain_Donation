/**
 * Cardano Wallet Connector
 * 
 * Provides functionality to connect to various Cardano wallets
 * including Eternl, Nami, and Flint
 */

const walletConnector = {
    /**
     * Check if a specific wallet is available in the browser
     * @param {string} walletName - The name of the wallet to check: 'eternl', 'nami', or 'flint'
     * @returns {boolean} - Whether the wallet is available
     */
    isWalletAvailable: function(walletName) {
        if (!window.cardano) return false;
        
        switch(walletName.toLowerCase()) {
            case 'eternl':
                return !!window.cardano.eternl;
            case 'nami':
                return !!window.cardano.nami;
            case 'flint':
                return !!window.cardano.flint;
            default:
                return false;
        }
    },
    
    /**
     * Connect to a specified wallet
     * @param {string} walletName - The name of the wallet to connect to
     * @returns {Promise<object>} - Result object with success status and wallet info
     */
    connect: async function(walletName) {
        try {
            // Check if the wallet is available
            if (!this.isWalletAvailable(walletName)) {
                return {
                    success: false,
                    error: `${walletName} wallet not found. Please install the extension.`
                };
            }
            
            // Get wallet API
            const walletAPI = await this._getWalletAPI(walletName);
            
            if (!walletAPI) {
                return {
                    success: false,
                    error: `Could not connect to ${walletName} API.`
                };
            }
            
            // Request wallet connection/permission
            const connected = await this._requestWalletPermission(walletAPI);
            
            if (!connected) {
                return {
                    success: false,
                    error: `User rejected ${walletName} connection.`
                };
            }
            
            // Get wallet information
            const address = await this._getWalletAddress(walletAPI, walletName);
            
            // If address is not available, return error
            if (address === "Address not available" || address === "Error retrieving address") {
                return {
                    success: false,
                    error: `Could not retrieve wallet address. Please make sure the DApp account is correctly set up in ${walletName} wallet.`,
                    details: "To set up a DApp account, open your wallet, click the connection icon in the top-right, select your account, and click 'Connect As DApp Account'."
                };
            }
            
            const balance = await this._getWalletBalance(walletAPI);
            const network = await this._getWalletNetwork(walletAPI);
            
            return {
                success: true,
                walletName: walletName,
                address: address,
                balance: balance,
                network: network
            };
            
        } catch (error) {
            console.error("Wallet connection error:", error);
            return {
                success: false,
                error: error.message || `Error connecting to ${walletName}`
            };
        }
    },
    
    /**
     * Sign transaction with wallet
     * @param {string} walletName - The name of the wallet to use for signing
     * @param {string} txCborHex - CBOR hex string of the transaction to sign
     * @returns {Promise<object>} - Result with signature status and witness
     */
    signTransaction: async function(walletName, txCborHex) {
        try {
            // Get wallet API
            const walletAPI = await this._getWalletAPI(walletName);
            
            if (!walletAPI || !walletAPI.signTx) {
                return {
                    success: false,
                    error: `Could not access ${walletName} signing API.`
                };
            }
            
            // Request transaction signing
            const witnessSet = await walletAPI.signTx(txCborHex, true);
            
            return {
                success: true,
                witness: witnessSet
            };
            
        } catch (error) {
            console.error("Transaction signing error:", error);
            return {
                success: false,
                error: error.message || `Error signing transaction with ${walletName}`
            };
        }
    },
    
    /**
     * Submit signed transaction to the network via wallet
     * @param {string} walletName - The name of the wallet to use
     * @param {string} txCborHex - CBOR hex string of the signed transaction
     * @returns {Promise<object>} - Result with submission status and transaction hash
     */
    submitTransaction: async function(walletName, txCborHex) {
        try {
            // Get wallet API
            const walletAPI = await this._getWalletAPI(walletName);
            
            if (!walletAPI || !walletAPI.submitTx) {
                return {
                    success: false,
                    error: `Could not access ${walletName} submission API.`
                };
            }
            
            // Submit transaction
            const txHash = await walletAPI.submitTx(txCborHex);
            
            return {
                success: true,
                txHash: txHash
            };
            
        } catch (error) {
            console.error("Transaction submission error:", error);
            return {
                success: false,
                error: error.message || `Error submitting transaction with ${walletName}`
            };
        }
    },
    
    /**
     * Get a wallet's API instance
     * @private
     * @param {string} walletName - The name of the wallet
     * @returns {Promise<object>} - The wallet API object
     */
    _getWalletAPI: async function(walletName) {
        if (!window.cardano) return null;
        
        switch(walletName.toLowerCase()) {
            case 'eternl':
                return window.cardano.eternl;
            case 'nami':
                return window.cardano.nami;
            case 'flint':
                return window.cardano.flint;
            default:
                return null;
        }
    },
    
    /**
     * Request permission to connect to the wallet
     * @private
     * @param {object} walletAPI - The wallet API object
     * @returns {Promise<boolean>} - Whether permission was granted
     */
    _requestWalletPermission: async function(walletAPI) {
        try {
            if (!walletAPI || !walletAPI.enable) {
                return false;
            }
            
            await walletAPI.enable();
            return true;
        } catch (error) {
            console.error("Wallet permission error:", error);
            return false;
        }
    },
    
    /**
     * Get the wallet's address
     * @private
     * @param {object} walletAPI - The wallet API object
     * @param {string} walletName - The name of the wallet
     * @returns {Promise<string>} - The wallet address
     */
    _getWalletAddress: async function(walletAPI, walletName) {
        try {
            if (!walletAPI) {
                return "Address not available";
            }
            
            // Different approaches for different wallets
            // Eternl specific handling
            if (walletName === 'eternl') {
                try {
                    // First try the standard API methods
                    if (walletAPI.getUsedAddresses) {
                        const addresses = await walletAPI.getUsedAddresses();
                        if (addresses && addresses.length > 0) {
                            return addresses[0];
                        }
                    }
                    
                    // Try getting the reward address (which is often more reliable in Eternl)
                    if (walletAPI.getRewardAddresses) {
                        const rewardAddresses = await walletAPI.getRewardAddresses();
                        if (rewardAddresses && rewardAddresses.length > 0) {
                            // Get the staking address ID which can help identify the wallet
                            console.log("Reward address available:", rewardAddresses[0]);
                        }
                    }
                    
                    // Fallback to unused addresses
                    if (walletAPI.getUnusedAddresses) {
                        const unusedAddresses = await walletAPI.getUnusedAddresses();
                        if (unusedAddresses && unusedAddresses.length > 0) {
                            return unusedAddresses[0];
                        }
                    }
                    
                    // Final attempt with change address
                    if (walletAPI.getChangeAddress) {
                        const changeAddress = await walletAPI.getChangeAddress();
                        return changeAddress;
                    }
                    
                    // Try the new Eternl v2 API if available
                    if (walletAPI.getBaseAddress) {
                        return await walletAPI.getBaseAddress();
                    }
                    
                    // If we get here, we couldn't get the address through regular means
                    // This likely means the user hasn't set up their DApp account in Eternl
                    return "Address not available";
                } catch (eternlError) {
                    console.error("Eternl specific error:", eternlError);
                    return "Error retrieving address";
                }
            }
            
            // Generic approach for other wallets
            if (walletAPI.getUsedAddresses) {
                const addresses = await walletAPI.getUsedAddresses();
                if (addresses && addresses.length > 0) {
                    return addresses[0];
                }
            }
            
            // Fallback to unused addresses
            if (walletAPI.getUnusedAddresses) {
                const unusedAddresses = await walletAPI.getUnusedAddresses();
                if (unusedAddresses && unusedAddresses.length > 0) {
                    return unusedAddresses[0];
                }
            }
            
            // Final fallback for different wallet APIs
            if (walletAPI.getChangeAddress) {
                return await walletAPI.getChangeAddress();
            }
            
            return "Address not available";
        } catch (error) {
            console.error("Error getting wallet address:", error);
            return "Error retrieving address";
        }
    },
    
    /**
     * Get the wallet's balance
     * @private
     * @param {object} walletAPI - The wallet API object
     * @returns {Promise<string>} - The wallet balance in ADA
     */
    _getWalletBalance: async function(walletAPI) {
        try {
            if (!walletAPI || !walletAPI.getBalance) {
                return "Balance not available";
            }
            
            const balance = await walletAPI.getBalance();
            // Convert balance to ADA (lovelace to ADA: divide by 1,000,000)
            if (balance) {
                const balanceInAda = parseInt(balance) / 1000000;
                return balanceInAda.toFixed(2);
            }
            
            return "Balance not available";
        } catch (error) {
            console.error("Error getting wallet balance:", error);
            return "Error retrieving balance";
        }
    },
    
    /**
     * Get the wallet's network information
     * @private
     * @param {object} walletAPI - The wallet API object
     * @returns {Promise<string>} - The network name
     */
    _getWalletNetwork: async function(walletAPI) {
        try {
            if (!walletAPI || !walletAPI.getNetworkId) {
                return "Network not available";
            }
            
            const networkId = await walletAPI.getNetworkId();
            
            // Convert network ID to name
            switch(networkId) {
                case 0:
                    return "Testnet";
                case 1:
                    return "Mainnet";
                default:
                    return `Network ID: ${networkId}`;
            }
        } catch (error) {
            console.error("Error getting wallet network:", error);
            return "Error retrieving network";
        }
    }
}; 