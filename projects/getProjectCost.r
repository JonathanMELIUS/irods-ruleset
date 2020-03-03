# Call with
#
# irule -F getProjectCost.r "*project='P000000001'"
#
# Output variables:
# *result: whole project storage cost
# *collections: nested json array for each collection cost
# stdout -> *result
#
# Please note the different usage of size units:
# - bytes are used for the purpose of storing values in iCAT
# - GB is used for the purpose of calculating and displaying costs
# - GiB is used for the purpose of diplaying the size to end-user

irule_dummy() {
    IRULE_getProjectCost(*project, *result, *collections, *projectSize);

    writeLine("stdout", *result);
}

IRULE_getProjectCost(*project, *result, *collections, *projectSize) {
    *pricePerGBPerYearAttr = "NCIT:C88193";
    *collectionsArray = "[]";
    *collectionsArraySize = 0;
    *projectCost = 0;
    *projectSize = 0;
    *result = 0;

    # Key pair Value object to store *pricePerGBPerYear for each resource:
    # key -> resource ID
    # value ->  *pricePerGBPerYear
    *resources;
    # Need a init KpV or fail when it's empty at the price's lookup
    *resources.init = "0";

    # Flag variable to keep the last COLL_NAME inserted into *collectionsArray
    # Warning: expected first default value. Need a more robust check
    *previousCollection = "/nlmumc/projects/*project/C000000001";
    *resourceDetails = '[]';
    *detailsArraySize = 0;
    *collectionCost = 0;

    # Prepare and execute query
    # INFO: The order of elements in *param will influence the alphabetical sorting of the result set.
    # Here, all results from the same COLL_NAME group together (1st level sort), then ascending on META_COLL_ATTR_NAME (2nd level sort), etc.
    *param = "COLL_NAME, META_COLL_ATTR_NAME, META_COLL_ATTR_VALUE";
    *cond = "META_COLL_ATTR_NAME like 'dcat:byteSize_resc_%' and COLL_PARENT_NAME = '/nlmumc/projects/*project'";
    msiMakeGenQuery(*param, *cond, *Query);
    msiExecGenQuery(*Query, *QOut);
    # Gets the continue index value generated by msiExecGenQuery
    # Determine whether there are remaining rows to retrieve from the generated query
    msiGetContInxFromGenQueryOut(*QOut, *cont);
    while (*cont  >= 0){
        # Loop over SQL result and calculate the cost of this project
        foreach (*Row in *QOut){
            *projectCollection = *Row.COLL_NAME;
            *resourceId = triml(*Row.META_COLL_ATTR_NAME, "dcat:byteSize_resc_");

            # We're looping over byteSize_resc_* AVUs for an entire project at once. If files in 1 collection are stored over multiple resources,
            # there will be multiple rows for that collection in *QOut. We need to keep track of the collection that we're processing
            # and compare that to the collection of the previous iteration of the loop.
            # When the current *Row has a different COLL_NAME than the previous iteration, we sum the size and costs, finalize the json
            # for the previous collection and reset everything before continuing the loop.
            if (*previousCollection != *projectCollection){
                # Get the total size of this collection in GiB (for displaying)
                getCollectionSize(*previousCollection, "GiB", "none", *collSize);
                *projectSize = *projectSize + double(*collSize);

                uuChopPath(*previousCollection, *dir, *collectionId);
                *collection = '{"collection": "*collectionId", "dataSizeGiB": "*collSize", "detailsPerResource": *resourceDetails, "collectionStorageCost": "*collectionCost"}';

                # Add the results of the previous collection to the Json
                msi_json_arrayops(*collectionsArray, *collection, "add", *collectionsArraySize);
                *projectCost = *projectCost + *collectionCost;

                # Reset
                *previousCollection = *projectCollection;
                *resourceDetails = '[]';
                *collectionCost = 0;
            }

            # Lookup the price for this resource
            *pricePerGBPerYearStr = "";
            *queryForPriceOnResource = true;
            # Use the cached KVP *resources object before even querying iCAT
            foreach(*ID in *resources){
                if ( *ID == *resourceId){
                    *pricePerGBPerYearStr = *resources.*ID;
                    *queryForPriceOnResource = false;
                    break;
                }
            }
            # Only query if *pricePerGBPerYearStr was not found in *resources
            if (*queryForPriceOnResource){
                *param = "META_RESC_ATTR_NAME, META_RESC_ATTR_VALUE";
                *cond = "RESC_ID = '*resourceId' and META_RESC_ATTR_NAME = '*pricePerGBPerYearAttr'";
                msiMakeGenQuery(*param, *cond, *Query_R);
                msiExecGenQuery(*Query_R, *QOut_R);
                foreach (*av in *QOut_R){
                    *resources."*resourceId" = *av.META_RESC_ATTR_VALUE;
                    *pricePerGBPerYearStr = *av.META_RESC_ATTR_VALUE;
                }
                msiCloseGenQuery(*Query_R, *QOut_R);
            }

            if (*pricePerGBPerYearStr == ""){
                failmsg(-1, "Resource ID '*resourceId': no attribute called '*pricePerGBPerYearAttr' found");
            }

            # Convert to GB (for calculation and display of costs)
            *sizeOnResource = double(*Row.META_COLL_ATTR_VALUE)/1000/1000/1000;

            # Calculate cost
            *storageCostOnResc = *sizeOnResource * double(*pricePerGBPerYearStr);
            *collectionCost = *collectionCost + *storageCostOnResc;

            # Add the results for this resource to the Json
            *details = '{"resource": "*resourceId", "dataSizeGBOnResource": "*sizeOnResource", "pricePerGBPerYear": "*pricePerGBPerYearStr", "storageCostOnResource": "*storageCostOnResc"}';
            msi_json_arrayops(*resourceDetails, *details, "add", *detailsArraySize);

            # Error out if no byteSize_resc attribute is present for this collection
            if ( *resourceId == "" ) {
                msiWriteRodsLog("WARNING: *projectCollection: no attribute 'dcat:byteSize_resc_<RescID>' found. Using default value of '*collectionCost'", 0);
            }
        }
        if (*cont  == 0){
            # If the continuation index is 0 the query will be closed
            break;
        }
        msiGetMoreRows(*Query, *QOut, *cont);
    }
    msiCloseGenQuery(*Query, *QOut);
    # Append last *collection iteration in *collectionsArray
    if (*resourceDetails != "[]"){
        getCollectionSize(*projectCollection, "GiB", "none", *collSize);
        *projectSize = *projectSize + double(*collSize);

        uuChopPath(*previousCollection, *dir, *collectionId);
        *collection = '{"collection": "*collectionId", "dataSizeGiB": "*collSize", "detailsPerResource": *resourceDetails, "collectionStorageCost": "*collectionCost"}';

        *projectCost = *projectCost + *collectionCost;
        msi_json_arrayops(*collectionsArray, *collection, "add", *collectionsArraySize);
    }
    # Output the results for the entire project as Json
    *collections = *collectionsArray;
    *result = *projectCost;
}

INPUT *project=""
OUTPUT ruleExecOut

