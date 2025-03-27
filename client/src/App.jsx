import { AppRouter, Header } from './components'
import { BrowserRouter } from 'react-router'
const App = () => {
  return (
	  <BrowserRouter>
		  <Header/>
			<AppRouter />
		</BrowserRouter>
  )
}

export default App