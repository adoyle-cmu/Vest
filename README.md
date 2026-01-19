# Heirloom Head Right Calculator

A simple Python application with an interactive GUI to help abstractors and attorneys divide heirs' claim to title head rights.

## Description

This application allows you to build an inheritance tree to track the division of property leasing rights. You can start with one or more original owners and then add heirs with their respective shares. The application will calculate and display the final ownership for each claimant.

## Features

-   Add multiple original owners (trunks).
-   Add heirs to any person in the inheritance tree.
-   Specify shares as fractions (e.g., 1/2, 1/3).
-   Generate a report of all current claimants and their final shares, both as fractions and percentages.

## How to Run

1.  Make sure you have Python 3 installed.
2.  Run the `main.py` file:
    ```bash
    python main.py
    ```

## How to Use

1.  Click "Add Original Owner" to add the initial owner(s) of the property.
2.  Select a person in the tree and click "Add Heir" to add a successor. You will be prompted to enter the heir's name and their share of the inheritance from the selected person.
3.  Continue adding heirs to build the complete inheritance tree.
4.  Once the tree is complete, click "Generate Report" to view a list of all the current claimants (leaves of the tree) and their calculated leasing right portions.
