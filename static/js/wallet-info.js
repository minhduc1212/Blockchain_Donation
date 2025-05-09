// Function to check if wallet is connected and update UI
function checkWalletConnection() {
    const walletConnectContainer = document.getElementById('wallet-connect-container');
    if (!walletConnectContainer) return;
    
    const storedAddress = localStorage.getItem('sender_address');
    
    if (storedAddress) {
        // Update the wallet connection display with dropdown
        updateWalletDisplay(storedAddress);
        
        // Fetch additional wallet info if not already loaded
        if (!walletConnectContainer.getAttribute('data-loaded')) {
            fetchWalletInfo(storedAddress);
            walletConnectContainer.setAttribute('data-loaded', 'true');
        }
    } else {
        // Display default wallet connection button
        walletConnectContainer.innerHTML = `
            <a class="connect-wallet" href="/connect_wallet">
                <i class="fa-solid fa-wallet" style="margin-right: 0.5rem;"></i>
                Connect Wallet
            </a>
        `;
    }
}

// Update the wallet display with abbreviated address
function updateWalletDisplay(address) {
    const walletConnectContainer = document.getElementById('wallet-connect-container');
    if (!walletConnectContainer) return;
    
    walletConnectContainer.innerHTML = `
        <div class="wallet-dropdown">
            <a class="connect-wallet connected-wallet" href="/connect_wallet">
                <i class="fa-solid fa-wallet"></i>
                Connected: ${address.substring(0, 8)}...
            </a>
            <div class="wallet-dropdown-content" id="wallet-info-dropdown">
                <div class="wallet-info-item">
                    <span class="wallet-info-label">Address:</span>
                    <span class="wallet-info-value">
                        ${address.substring(0, 10)}...${address.substring(address.length - 8)}
                        <i class="fa-solid fa-copy wallet-address-copy" onclick="copyWalletAddress('${address}')" title="Copy full address"></i>
                    </span>
                </div>
                <div id="wallet-details-loading">
                    <div class="d-flex align-items-center justify-content-center my-2">
                        <div class="spinner-border spinner-border-sm" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <span class="ms-2 small">Loading wallet information...</span>
                    </div>
                </div>
                <hr>
                <div class="text-center">
                    <button class="btn btn-sm btn-outline-danger" onclick="disconnectWallet()">Disconnect</button>
                </div>
            </div>
        </div>
    `;
}

// Fetch wallet information from the server
function fetchWalletInfo(walletAddress) {
    const walletInfoDropdown = document.getElementById('wallet-info-dropdown');
    if (!walletInfoDropdown) return;
    
    fetch('/api/wallet_info', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wallet_address: walletAddress })
    })
    .then(response => response.json())
    .then(data => {
        const loadingDiv = document.getElementById('wallet-details-loading');
        if (!loadingDiv) return;
        
        if (data.error) {
            // Show limited info if there was an error
            const networkInfo = data.network || 'Unknown';
            loadingDiv.outerHTML = `
                <div class="wallet-info-item">
                    <span class="wallet-info-label">Network:</span>
                    <span class="wallet-info-value ${networkInfo === 'Testnet' ? 'text-warning' : 'text-success'}">${networkInfo}</span>
                </div>
                <div class="wallet-info-item text-danger">
                    <span class="wallet-info-label">Balance:</span>
                    <span class="wallet-info-value">Could not fetch</span>
                </div>
            `;
        } else {
            // Show full wallet information
            loadingDiv.outerHTML = `
                <div class="wallet-info-item">
                    <span class="wallet-info-label">Network:</span>
                    <span class="wallet-info-value ${data.network === 'Testnet' ? 'text-warning' : 'text-success'}">${data.network}</span>
                </div>
                <div class="wallet-info-item">
                    <span class="wallet-info-label">Balance:</span>
                    <span class="wallet-info-value">${typeof data.balance_ada === 'number' ? data.balance_ada.toFixed(2) : data.balance_ada} ADA</span>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error fetching wallet info:', error);
        const loadingDiv = document.getElementById('wallet-details-loading');
        if (loadingDiv) {
            loadingDiv.outerHTML = `
                <div class="wallet-info-item text-danger">
                    <span class="wallet-info-label">Status:</span>
                    <span class="wallet-info-value">Error fetching wallet data</span>
                </div>
            `;
        }
    });
}

// Copy wallet address to clipboard
function copyWalletAddress(address) {
    navigator.clipboard.writeText(address)
        .then(() => {
            // Show a tooltip or notification that address was copied
            showToast('success', 'Address copied to clipboard');
        })
        .catch(err => {
            console.error('Could not copy address: ', err);
            showToast('error', 'Failed to copy address');
        });
}

// Create and initialize the wallet disconnect confirmation modal
function createDisconnectModal() {
    // Check if modal already exists
    if (document.getElementById('disconnectWalletModal')) {
        return;
    }
    
    // Create the modal HTML
    const modalHTML = `
    <div class="modal fade" id="disconnectWalletModal" tabindex="-1" aria-labelledby="disconnectWalletModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-warning">
                    <h5 class="modal-title" id="disconnectWalletModalLabel">Disconnect Wallet</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to disconnect your wallet?</p>
                    <p class="mb-0 text-muted small">You will need to reconnect your wallet to create campaigns or make donations.</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-warning" id="confirm-disconnect-btn">Disconnect</button>
                </div>
            </div>
        </div>
    </div>`;
    
    // Append modal to body
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add event listener for confirm disconnect button
    document.getElementById('confirm-disconnect-btn').addEventListener('click', function() {
        // Hide the modal
        bootstrap.Modal.getInstance(document.getElementById('disconnectWalletModal')).hide();
        
        // Disconnect wallet
        localStorage.removeItem('sender_address');
        showToast('info', 'Wallet disconnected');
        
        // Refresh page after a short delay
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    });
}

// Update the disconnectWallet function to show the modal
function disconnectWallet() {
    // Create modal if it doesn't exist
    createDisconnectModal();
    
    // Show the modal
    new bootstrap.Modal(document.getElementById('disconnectWalletModal')).show();
}

// Simple toast notification
function showToast(type, message) {
    // Check if notification container exists, if not create it
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; max-width: 350px;';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.style.cssText = `
        background-color: #ffffff;
        border-left: 4px solid ${type === 'success' ? '#28a745' : (type === 'error' ? '#dc3545' : '#17a2b8')};
        box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
        margin-bottom: 10px;
    `;
    
    toast.innerHTML = `
        <div class="toast-header">
            <i class="fa-solid ${type === 'success' ? 'fa-circle-check text-success' : 
                            (type === 'error' ? 'fa-circle-exclamation text-danger' : 'fa-circle-info text-info')} me-2"></i>
            <strong class="me-auto">Wallet</strong>
            <small>just now</small>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
        <div class="toast-body">
            <p class="mb-0">${message}</p>
        </div>
    `;
    
    // Add to container
    container.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkWalletConnection();
}); 