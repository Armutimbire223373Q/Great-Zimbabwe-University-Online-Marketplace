class APIClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
            ...options.headers,
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'An error occurred');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Category endpoints
    async getCategories() {
        return this.request('/categories/');
    }

    async getSubcategories(categorySlug) {
        return this.request(`/categories/${categorySlug}/subcategories/`);
    }

    // Listing endpoints
    async getListings(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/listings/${queryString ? `?${queryString}` : ''}`);
    }

    async getListing(id) {
        return this.request(`/listings/${id}/`);
    }

    async createListing(data) {
        return this.request('/listings/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateListing(id, data) {
        return this.request(`/listings/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteListing(id) {
        return this.request(`/listings/${id}/`, {
            method: 'DELETE',
        });
    }

    async addToCart(listingId, quantity = 1) {
        return this.request(`/listings/${listingId}/add_to_cart/`, {
            method: 'POST',
            body: JSON.stringify({ quantity }),
        });
    }

    // Cart endpoints
    async getCart() {
        return this.request('/cart/');
    }

    async updateCartItem(cartId, itemId, quantity) {
        return this.request(`/cart/${cartId}/update_item/`, {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId, quantity }),
        });
    }

    async removeCartItem(cartId, itemId) {
        return this.request(`/cart/${cartId}/remove_item/`, {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId }),
        });
    }

    async checkout(cartId, data) {
        return this.request(`/cart/${cartId}/checkout/`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // Purchase endpoints
    async getPurchases() {
        return this.request('/purchases/');
    }

    async getPurchase(id) {
        return this.request(`/purchases/${id}/`);
    }

    async updatePurchaseStatus(id, status) {
        return this.request(`/purchases/${id}/update_status/`, {
            method: 'POST',
            body: JSON.stringify({ status }),
        });
    }

    async updatePaymentStatus(id, status) {
        return this.request(`/purchases/${id}/update_payment_status/`, {
            method: 'POST',
            body: JSON.stringify({ payment_status: status }),
        });
    }

    // Review endpoints
    async getReviews(userId) {
        return this.request(`/reviews/?reviewed=${userId}`);
    }

    async createReview(data) {
        return this.request('/reviews/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async markReviewHelpful(id) {
        return this.request(`/reviews/${id}/mark_helpful/`, {
            method: 'POST',
        });
    }

    async respondToReview(id, response) {
        return this.request(`/reviews/${id}/respond/`, {
            method: 'POST',
            body: JSON.stringify({ response }),
        });
    }
}

// Export the API client
window.api = new APIClient(); 