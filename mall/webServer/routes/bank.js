// modules
var cp = require('child_process');
var config = require('./config.js');
var q = require('./db.js');

var bank = {};

bank.now_check = false;


/*
 *  This function sets up loop for checking every minute.
 */
bank.checkAccount = function()
{
    console.log( 'Trigger timer');
    if ( this.now_check == false )
        this.now_check = setInterval( bank.connectBank, config.TIME_TO_CHECK );
};


/*
 *  This function disables the above loop for checking every minute.
 */
bank.stopCheck = function()
{
    console.log( 'Timer stop');
    clearInterval( this.now_check );
    this.now_check = false;
}


/*
 * This function is called as a callback function 1 minute after purchasing item.
 * TODO : this function is implemented, but not tested fully because other team's dependency...
 *        So we just implemented the simple scenario with dummy data...
 *        and we said this situation to the professor...
 *        He said these kind of integration issue will be continued next week.
 */
bank.connectBank = function( )
{
    console.log( 'Timer function');

    // SQL query for searching all the pending status orders
    var sString =  'SELECT orders.order_id AS id, orders.added_time AS time, \
                        orders.bank_account AS account, orders.bank_pw AS pw, \
                        SUM( order_items.product_num * products.price ) AS amount \
                    FROM ( orders JOIN order_items ) JOIN products \
                    ON ( orders.order_id = order_items.order_id ) \
                        AND ( order_items.product_id = products.product_id ) \
                    WHERE orders.status = "pending" \
                    GROUP BY orders.order_id ';

    var ipaddr = process.env.IPADDR.replace(/(.*)\.102/, "$1.101");

    // SQL handling
    q.query( sString, function( err, result, fields )
    {
        // when SQL error
        if (err) {
            console.log(err);
            return;
        }

        // when SQL success
        var items = result;

        // when there are no pending order, stop the checking loop
        if ( items.length == 0 )
            bank.stopCheck();

        items.forEach( function( item, index )
        {
            console.log( item );

            var time_now = new Date();
            var time_order = new Date( item.time );
            var ipaddr = process.env.IPADDR.replace(/(.*)\.102/, "$1.101");

            // console.log( time_now.getTime() );
            // console.log( time_order.getTime() );
            // console.log( time_order.getTime() + 60000 <= time_now.getTime() );

            // check before one minute
            if ( time_order.getTime() + 60000 > time_now.getTime() )
            {
                // check_transaction.py excution.
                // console.log("(" + item.account + "),(" + item.pw + "),(" + item.amount + ")\n\n");
                var check_result = cp.execSync( config.check_transaction
                                                + ' ' + ipaddr
                                                + ' ' + item.account
                                                + ' ' + item.pw + ' ' + item.amount );

                // console.log( check_result.toString() );
                // console.log( check_result.toString().substring(0,7) );

                if (check_result.toString().substring(0,7) == 'success')
                {
                    console.log('account checked.... success');

                    var uString = 'UPDATE orders SET status = "completed" WHERE order_id = ? ';

                    // update the status in order table
                    q.query( uString, [ item.id ], function( err, result, fields )
                    {
                        // when SQL error
                        if (err) {
                            console.log(err);
                            return;
                        }

                        // when SQL success
                        console.log(result);
                        return;
                    });

                    q.execute();

                    // remove_account.py excution.
                    cp.execSync( config.remove_account
                                 + ' ' + ipaddr
                                 + ' ' + item.account
                                 + ' ' + item.pw );

                    console.log('delete temporary account...');
                }
                else {
                    console.log('account checked.... fail');
                } // end else
            } // end if
            else {
                    var uString = 'UPDATE orders SET status = "abort" WHERE order_id = ? ';

                    // update the status in order table
                    q.query( uString, [ item.id ], function( err, result, fields )
                    {
                        // when SQL error
                        if (err) {
                            console.log(err);
                            return;
                        }

                        // when SQL success
                        console.log(result);

                        // remove_account.py excution.
                        cp.execSync( config.remove_account
                                     + ' ' + ipaddr
                                     + ' ' + item.account
                                     + ' ' + item.pw );

                        console.log('delete temporary account...');
                    }); // end SQL query

                    q.execute();
            }
        });  // end foreach
    }); // end SQL query

    q.execute();
};

bank.checkAccount();

module.exports = bank;
