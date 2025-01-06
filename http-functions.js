// Expose your site's functionality externally
// Follow instructions hear: https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/integrations/exposing-services/write-an-http-function
// to your Wix site Backend. Add the following in a file called 'http-functions.js'

import { ok, notFound, serverError } from "wix-http-functions";
import wixData  from "wix-data";

export function get_shoesListing(request) {
    let options = {
        "headers": {
            "Content-Type": "application/json"
        }
    };
    // Data you are interested with. All store products in my case
    let productsQuery = wixData.query("Stores/Products");

    return productsQuery
        .find()
        .then((results)=> {
            if (results.items.length > 0) {
                options.body = {
                    "items": results.items
                }
                return ok(options);
            }
            return notFound(options)
        })
        .catch((error)=> {
            options.body = {
                "error": error.message
            };
            return serverError(options);
        });
}
