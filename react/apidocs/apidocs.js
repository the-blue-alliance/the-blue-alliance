import React, { Component} from 'react';
import ReactDOM from 'react-dom';
import ApiDocsFrame from './ApiDocsFrame'

const swagger_url = document.getElementById('swagger_url').innerHTML
ReactDOM.render(
  <ApiDocsFrame url={swagger_url}/>,
  document.getElementById('content')
);