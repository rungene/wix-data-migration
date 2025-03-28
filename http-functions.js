// Expose your site's functionality externally
// Follow instructions hear: https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/integrations/exposing-services/write-an-http-function
// to your Wix site Backend. Add the following in a file called 'http-functions.js'
import { ok, notFound, serverError } from "wix-http-functions";
import wixData from "wix-data";

export async function get_storeListing(request) {
    let options = {
        "headers": {
            "Content-Type": "application/json"
        }
    };

    try {
        let allItems = [];
        let results = await wixData.query("Stores/Products").limit(100).find();

        allItems = allItems.concat(results.items);

        // Keep fetching next pages until all data is retrieved
        while (results.hasNext()) {
            results = await results.next();  // Await each next page
            allItems = allItems.concat(results.items);
        }

        if (allItems.length > 0) {
            options.body = { "items": allItems };
            return ok(options);
        }

        return notFound(options);

    } catch (error) {
        options.body = { "error": error.message };
        return serverError(options);
    }
}
