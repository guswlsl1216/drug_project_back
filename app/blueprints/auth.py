from flask import Blueprint, request, jsonify
from email_validator import validate_email, EmailNotValidError
from extensions import db
