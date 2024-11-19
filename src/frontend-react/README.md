# Frontend React App

This container will launch a user-friendly application built using a REACT framework that will interact with our API Service.

## Prerequisites
* Have Docker installed
* Cloned this repository to your local machine https://github.com/ghattisu/AC215_Bloodwise

## Run Container
- Make sure you are inside the `frontend-react` folder and open a terminal at this location
- Make sure that Docker Desktop is enabled and running
- Run `sh docker-shell.sh`


## Dependencies Installation
First time only: Install the required Node packages using: `npm install`

## Launch Development Server
1. Start the development server: ` npm run dev`

2. View your app at: http://localhost:3000

> Note: Make sure the API service container is running for full functionality
## Review App
- Go to Home page and try Chat Assistant

## Review App Code
- Open folder `frontend-react/src`

## Data Services
- Data Service (`src/services/DataService.js`)
- Review Data Service methods that connects frontend to all backend APIs

## App Pages
- Open folder `frontend-react/src/app`
- Review the main app page:
  - Chat Assistant (`src/app/chat/page.jsx`)

## App Components
- Open folder `frontend-react/src/components`
- Review components of the app
  - Layout for common components such as Header, Footer
  - Chat for all the chat components

## Review Container Configuration
- Check `docker-shell.sh`: 
  - Port mapping: `-p 9000:9000`
  - Development mode: `-e DEV=1`
- Check `docker-entrypoint.sh`: Dev vs. Production settings
