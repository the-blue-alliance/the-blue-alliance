import { combineReducers } from 'redux'
import auth from './auth'

const eventwizardReducer = combineReducers({
  auth,
})

export default eventwizardReducer
