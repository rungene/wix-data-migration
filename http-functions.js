// Expose your site's functionality externally
// Follow instructions hear: https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/integrations/exposing-services/write-an-http-function
// to your Wix site Backend. Add the following in a file called 'http-functions.js'
import { ok, badRequest, serverError } from "wix-http-functions";
import wixData  from "wix-data";

export async function get_storeListing(request) {
    const queryParams = request.query;
    const page = parseInt(queryParams.page || "0");
    const limit = parseInt(queryParams.limit || "50");

    const options = {
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (limit > 100 || limit < 1) {
        options.body = { error: "Limit must be between 1 and 100." };
        return badRequest(options);
    }

    try {
        const results = await wixData.query("Stores/Products")
            .skip(page * limit)
            .limit(limit)
            .find();


        options.body = {
            items: results.items,
            hasNext: results.hasNext(),
            currentPage: page
        };

        return ok(options);
    } catch (error) {
        options.body = { error: error.message };
        return serverError(options);
    }
}
