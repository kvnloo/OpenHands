import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CurriculumSkillsTab: React.FC = () => {
    const [curriculum, setCurriculum] = useState(null);
    const [skills, setSkills] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchCurriculumAndSkills = async () => {
            setLoading(true);
            try {
                const curriculumResponse = await axios.get('/api/automatic-curriculum');
                const skillsResponse = await axios.get('/api/skill-library');
                setCurriculum(curriculumResponse.data);
                setSkills(skillsResponse.data);
            } catch (err) {
                if (err instanceof Error) {
                    setError(err.message);
                } else {
                    setError('An unknown error occurred');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchCurriculumAndSkills();
    }, []);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            <h1>Curriculum & Skills</h1>
            <div>
                <h2>Automatic Curriculum</h2>
                <pre>{JSON.stringify(curriculum, null, 2)}</pre>
            </div>
            <div>
                <h2>Skill Library</h2>
                <pre>{JSON.stringify(skills, null, 2)}</pre>
            </div>
        </div>
    );
};

export default CurriculumSkillsTab;
