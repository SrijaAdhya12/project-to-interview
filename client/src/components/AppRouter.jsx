import { Route, Routes, useLocation } from 'react-router'
import { RepoAnalyzer, RepoChatbot, RepoReview } from '.'

const AppRouter = () => {
	const location = useLocation()
	return (
		<Routes location={location}>
			<Route path="/" element={<RepoAnalyzer />} />
			<Route path="/code-analysis" element={<RepoReview />} />
			<Route path="/chatbot" element={<RepoChatbot />} />

		</Routes>
	)
}

export default AppRouter
