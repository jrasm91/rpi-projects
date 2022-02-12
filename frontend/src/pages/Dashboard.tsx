import { Divider, Button, Heading, Box } from '@chakra-ui/react';
import { ReactNode } from 'react';
import { Layout } from '../components/Layout';

interface CardProps {
  children?: ReactNode;
}

function Card({ children }: CardProps) {
  return (
    <Box my='4' p='4' boxShadow='md' bg='white'>
      {children}
    </Box>
  );
}

function Dashboard() {
  return (
    <Layout>
      <Card>
        <Heading size='lg'>Zones</Heading>
        <Divider my='3'></Divider>
      </Card>
      <Card>
        <Heading size='lg'>Zones</Heading>
        <Divider my='3'></Divider>
      </Card>

      <Card>
        <Heading size='lg'>Queue</Heading>
        <Divider my='3'></Divider>
      </Card>
    </Layout>
  );
}

export default Dashboard;
