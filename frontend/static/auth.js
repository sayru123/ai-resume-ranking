// Authentication service using AWS Cognito - FIXED WITH CONFIRMATION
class AuthService {
    constructor() {
        this.cognitoUser = null;
        this.session = null;
        this.pendingUser = null; // Store user waiting for confirmation
        this.initAWS();
    }

    initAWS() {
        AWS.config.region = window.AWS_CONFIG.region;
        
        this.userPool = new AmazonCognitoIdentity.CognitoUserPool({
            UserPoolId: window.AWS_CONFIG.userPoolId,
            ClientId: window.AWS_CONFIG.userPoolWebClientId
        });

        this.cognitoUser = this.userPool.getCurrentUser();
        if (this.cognitoUser) {
            this.cognitoUser.getSession((err, session) => {
                if (err) {
                    console.log('Session error:', err);
                    return;
                }
                this.session = session;
                this.updateUI();
            });
        }
    }

    async signUp(email, password, name) {
        return new Promise((resolve, reject) => {
            const attributeList = [
                new AmazonCognitoIdentity.CognitoUserAttribute({
                    Name: 'email',
                    Value: email
                }),
                new AmazonCognitoIdentity.CognitoUserAttribute({
                    Name: 'name',
                    Value: name
                }),
                new AmazonCognitoIdentity.CognitoUserAttribute({
                    Name: 'given_name',
                    Value: name.split(' ')[0] || name
                }),
                new AmazonCognitoIdentity.CognitoUserAttribute({
                    Name: 'family_name',
                    Value: name.split(' ').slice(1).join(' ') || 'User'
                })
            ];

            // Generate unique username (not email format)
            const username = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);

            this.userPool.signUp(username, password, attributeList, null, (err, result) => {
                if (err) {
                    reject(err);
                    return;
                }
                
                // Store the user for confirmation
                this.pendingUser = result.user;
                resolve(result);
            });
        });
    }

    async confirmSignUp(verificationCode) {
        return new Promise((resolve, reject) => {
            if (!this.pendingUser) {
                reject(new Error('No pending user to confirm'));
                return;
            }

            this.pendingUser.confirmRegistration(verificationCode, true, (err, result) => {
                if (err) {
                    reject(err);
                    return;
                }
                
                // Clear pending user after successful confirmation
                this.pendingUser = null;
                resolve(result);
            });
        });
    }

    async signIn(email, password) {
        return new Promise((resolve, reject) => {
            const authenticationData = {
                Username: email,
                Password: password
            };

            const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
            
            const userData = {
                Username: email,
                Pool: this.userPool
            };

            this.cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

            this.cognitoUser.authenticateUser(authenticationDetails, {
                onSuccess: (session) => {
                    this.session = session;
                    this.updateUI();
                    resolve(session);
                },
                onFailure: (err) => {
                    reject(err);
                }
            });
        });
    }

    signOut() {
        if (this.cognitoUser) {
            this.cognitoUser.signOut();
            this.cognitoUser = null;
            this.session = null;
            this.updateUI();
        }
    }

    isAuthenticated() {
        return this.session && this.session.isValid();
    }

    getIdToken() {
        if (this.session) {
            return this.session.getIdToken().getJwtToken();
        }
        return null;
    }

    updateUI() {
        const authSection = document.getElementById('auth-section');
        const mainContent = document.getElementById('main-content');
        const userInfo = document.getElementById('user-info');

        if (this.isAuthenticated()) {
            authSection.style.display = 'none';
            mainContent.style.display = 'block';
            
            if (this.session) {
                const payload = this.session.getIdToken().payload;
                userInfo.innerHTML = '<div class="flex items-center space-x-4"><span class="text-sm text-gray-600">Welcome, ' + (payload.name || payload.email) + '</span><button onclick="authService.signOut()" class="text-sm text-red-600 hover:text-red-800">Sign Out</button></div>';
            }
            
            if (window.loadDashboard) {
                window.loadDashboard();
            }
        } else {
            authSection.style.display = 'block';
            mainContent.style.display = 'none';
            userInfo.innerHTML = '';
        }
    }
}

const authService = new AuthService();

document.addEventListener('DOMContentLoaded', function() {
    const signInForm = document.getElementById('signin-form');
    if (signInForm) {
        signInForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('signin-email').value;
            const password = document.getElementById('signin-password').value;
            
            try {
                await authService.signIn(email, password);
                document.getElementById('auth-error').textContent = '';
            } catch (error) {
                document.getElementById('auth-error').textContent = error.message;
                document.getElementById('auth-error').className = 'text-red-600 text-sm mt-2';
            }
        });
    }

    const signUpForm = document.getElementById('signup-form');
    if (signUpForm) {
        signUpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('signup-email').value;
            const password = document.getElementById('signup-password').value;
            const name = document.getElementById('signup-name').value;
            
            try {
                await authService.signUp(email, password, name);
                
                // Show confirmation code input
                showConfirmationForm(email);
                
            } catch (error) {
                document.getElementById('auth-error').textContent = error.message;
                document.getElementById('auth-error').className = 'text-red-600 text-sm mt-2';
            }
        });
    }

    // Confirmation form handler
    const confirmForm = document.getElementById('confirm-form');
    if (confirmForm) {
        confirmForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const code = document.getElementById('confirmation-code').value;
            
            try {
                await authService.confirmSignUp(code);
                document.getElementById('auth-error').textContent = 'Account confirmed! You can now sign in.';
                document.getElementById('auth-error').className = 'text-green-600 text-sm mt-2';
                
                // Switch back to sign in form
                setTimeout(() => {
                    hideConfirmationForm();
                    toggleAuthMode(); // Switch to sign in
                }, 2000);
                
            } catch (error) {
                document.getElementById('auth-error').textContent = error.message;
                document.getElementById('auth-error').className = 'text-red-600 text-sm mt-2';
            }
        });
    }

    window.toggleAuthMode = function() {
        const signInDiv = document.getElementById('signin-div');
        const signUpDiv = document.getElementById('signup-div');
        
        if (signInDiv.style.display === 'none') {
            signInDiv.style.display = 'block';
            signUpDiv.style.display = 'none';
        } else {
            signInDiv.style.display = 'none';
            signUpDiv.style.display = 'block';
        }
        
        document.getElementById('auth-error').textContent = '';
        hideConfirmationForm();
    };

    function showConfirmationForm(email) {
        const confirmDiv = document.getElementById('confirm-div');
        const signUpDiv = document.getElementById('signup-div');
        
        if (confirmDiv) {
            confirmDiv.style.display = 'block';
            signUpDiv.style.display = 'none';
            
            document.getElementById('auth-error').textContent = 'Account created! Please check your email (' + email + ') for the verification code.';
            document.getElementById('auth-error').className = 'text-green-600 text-sm mt-2';
        }
    }

    function hideConfirmationForm() {
        const confirmDiv = document.getElementById('confirm-div');
        if (confirmDiv) {
            confirmDiv.style.display = 'none';
        }
    }
});
