# Test project
The test assignments consist of improving and extending the grossly oversimplified, Django-based systems software of the fictional "nanobank". 

# Project setup
- [Install the `poetry` package manager](https://python-poetry.org/docs/#installation) if it's not on your system yet
- Run `poetry install --no-root` to install the project dependencies
- Start a shell with the project virtualenv activated and change to the source dir: 
    ```
    poetry shell
    cd src
    ```  
- Run migrations with `./manage.py migrate`
- Run tests to ensure that the env is ok `./manage.py test`


# Test assignments

## Scheduled payment
Implement the fundamentals of a "scheduled payment" feature for nanobank.

Clients will be able to define scheduled payments that will transfer a fixed amount from one account to another on a specific date every month. 

Your implementation needs to provide the necessary storage schema (models), a method to check which scheduled payments are due and a method to create the transaction for a payment that is due.

## Fix erratic `Transfer.do_transfer()` behavior
The `Transfer.do_transfer()` method is implemented naively and will cause problems when several operations are performed on a single account concurrently. For example, the sum of funds transferred from an account could be greater than its balance should allow. Identify what the problem is and fix it.

## Fix `Transfer.do_transfer()` accepting negative amounts
Update the Transfer.do_transfer() method to only accept values >0, Write a test that checks that only positive values are accepted and an exception is raised otherwise.

## Account / transfer schema evolution 
The current schema only allows for transfers between internal accounts - no transfers from/to accounts in other banks, no cash withdrawals or deposits - not very useful. Describe how you would extend the existing schema so that cash operations and transfers involving external accounts could be adequately stored. Actual schema changes are not required, place the description of your general approach as code comment in the `transfer.models` module. 
