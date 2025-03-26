import { AppRouter } from './components'
import { BrowserRouter } from 'react-router'
const App = () => {
  return (
		<BrowserRouter>
			<AppRouter />
		</BrowserRouter>
  )
}

export default App