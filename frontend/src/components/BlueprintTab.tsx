import React, { useState } from 'react';
import { useEffect } from 'react';
import axios from 'axios';

const BlueprintTab: React.FC = () => {
    const [blueprint, setBlueprint] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchBlueprint = async () => {
            setLoading(true);
            try {
                const response = await axios.post('/api/blueprint/generate', {
                    project_path: '/path/to/project'
                });
                setBlueprint(response.data.blueprint);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchBlueprint();
    }, []);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            <h1>Blueprint</h1>
            <pre>{JSON.stringify(blueprint, null, 2)}</pre>
        </div>
    );
};

export default BlueprintTab;
