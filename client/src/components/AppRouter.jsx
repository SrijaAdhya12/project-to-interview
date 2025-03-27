import { Route, Routes, useLocation } from 'react-router'
import { RepoAnalyzer, RepoReview } from '.'

const AppRouter = () => {
	const location = useLocation()
	return (
		<Routes location={location}>
			<Route path="/" element={<RepoAnalyzer />} />
			<Route path="/review" element={<RepoReview />} />
		</Routes>
	)
}

export default AppRouter
