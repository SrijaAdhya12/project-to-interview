import { FaGithub } from 'react-icons/fa'
import { Link } from 'react-router'

const Header = () => {
	return (
		<header className="bg-white shadow-sm">
			<div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
				<div className="flex items-center">
					<FaGithub className="h-8 w-8 text-gray-900" />
					<h1 className="ml-3 text-xl font-bold text-gray-900">Project to Interview</h1>
				</div>
				<nav className="flex space-x-6">
					<Link to="/" className="text-lg font-medium text-gray-900 hover:text-gray-700">
						Questions
					</Link>
					<Link to="/code-analysis" className="text-lg font-medium text-gray-900 hover:text-gray-700">
						Code Analysis
					</Link>
					<Link to="/chatbot" className="text-lg font-medium text-gray-900 hover:text-gray-700">
						Chatbot
					</Link>
				</nav>
			</div>
		</header>
	)
}

export default Header
