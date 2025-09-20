import { RealtimeAgent, tool } from '@openai/agents/realtime';

export const realEstateBrokerAgent = new RealtimeAgent({
  name: 'realEstateBroker',
  voice: 'sage',
  handoffDescription:
    "A professional real estate broker who helps clients with property searches, market analysis, property valuations, and real estate transactions. Handles both residential and commercial real estate inquiries.",

  instructions:
    `You are a knowledgeable and professional real estate broker. You help clients with:
    - Property searches based on their criteria (location, price, size, features)
    - Market analysis and property valuations
    - Guidance through buying/selling processes
    - Investment property advice
    - Neighborhood information and local market insights
    
    Be friendly, professional, and thorough in your responses. Always ask clarifying questions to better understand the client's needs and preferences.`,

  tools: [
    tool({
      name: 'searchProperties',
      description: 'Search for properties based on client criteria such as location, price range, property type, and features.',
      parameters: {
        type: 'object',
        properties: {
          location: {
            type: 'string',
            description: 'The desired location (city, neighborhood, or area)',
          },
          minPrice: {
            type: 'number',
            description: 'Minimum price range in USD',
          },
          maxPrice: {
            type: 'number',
            description: 'Maximum price range in USD',
          },
          propertyType: {
            type: 'string',
            enum: ['house', 'condo', 'townhouse', 'apartment', 'commercial', 'land', 'any'],
            description: 'Type of property the client is looking for',
          },
          bedrooms: {
            type: 'number',
            description: 'Minimum number of bedrooms required',
          },
          bathrooms: {
            type: 'number',
            description: 'Minimum number of bathrooms required',
          },
        },
        required: ['location'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { location, minPrice, maxPrice, propertyType, bedrooms, bathrooms } = input;
        
        // Simulated property data
        const properties = [
          {
            id: 'prop_001',
            address: '123 Oak Street, Downtown',
            price: 450000,
            type: 'house',
            bedrooms: 3,
            bathrooms: 2,
            sqft: 1800,
            features: ['garage', 'garden', 'updated kitchen']
          },
          {
            id: 'prop_002',
            address: '456 Maple Avenue, Suburbs',
            price: 320000,
            type: 'condo',
            bedrooms: 2,
            bathrooms: 2,
            sqft: 1200,
            features: ['balcony', 'gym', 'pool']
          },
          {
            id: 'prop_003',
            address: '789 Pine Road, Uptown',
            price: 650000,
            type: 'house',
            bedrooms: 4,
            bathrooms: 3,
            sqft: 2400,
            features: ['fireplace', 'large yard', 'modern appliances']
          },
        ];

        // Filter properties based on criteria
        let filteredProperties = properties.filter(prop => 
          prop.address.toLowerCase().includes(location.toLowerCase())
        );

        if (minPrice) {
          filteredProperties = filteredProperties.filter(prop => prop.price >= minPrice);
        }
        if (maxPrice) {
          filteredProperties = filteredProperties.filter(prop => prop.price <= maxPrice);
        }
        if (propertyType && propertyType !== 'any') {
          filteredProperties = filteredProperties.filter(prop => prop.type === propertyType);
        }
        if (bedrooms) {
          filteredProperties = filteredProperties.filter(prop => prop.bedrooms >= bedrooms);
        }
        if (bathrooms) {
          filteredProperties = filteredProperties.filter(prop => prop.bathrooms >= bathrooms);
        }

        return {
          properties: filteredProperties,
          totalFound: filteredProperties.length,
          searchCriteria: input
        };
      },
    }),

    tool({
      name: 'getPropertyDetails',
      description: 'Get detailed information about a specific property including photos, history, and neighborhood data.',
      parameters: {
        type: 'object',
        properties: {
          propertyId: {
            type: 'string',
            description: 'The unique ID of the property',
          },
        },
        required: ['propertyId'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { propertyId } = input;
        
        // Simulated detailed property data
        const propertyDetails = {
          id: propertyId,
          address: '123 Oak Street, Downtown',
          price: 450000,
          type: 'house',
          bedrooms: 3,
          bathrooms: 2,
          sqft: 1800,
          yearBuilt: 2015,
          lotSize: '0.25 acres',
          features: ['garage', 'garden', 'updated kitchen', 'hardwood floors', 'central air'],
          neighborhood: {
            walkScore: 85,
            schools: ['Oak Elementary (9/10)', 'Central High School (8/10)'],
            amenities: ['parks', 'shopping center', 'public transit']
          },
          marketData: {
            pricePerSqft: 250,
            daysOnMarket: 15,
            priceHistory: 'Listed 2 weeks ago, no price changes'
          }
        };

        return propertyDetails;
      },
    }),

    tool({
      name: 'scheduleViewing',
      description: 'Schedule a property viewing appointment for the client.',
      parameters: {
        type: 'object',
        properties: {
          propertyId: {
            type: 'string',
            description: 'The unique ID of the property to view',
          },
          clientName: {
            type: 'string',
            description: 'Name of the client',
          },
          clientPhone: {
            type: 'string',
            description: "Client's phone number",
          },
          preferredDate: {
            type: 'string',
            description: 'Preferred date for the viewing (e.g., "tomorrow", "this weekend", "next Tuesday")',
          },
          preferredTime: {
            type: 'string',
            description: 'Preferred time for the viewing (e.g., "morning", "afternoon", "2 PM")',
          },
        },
        required: ['propertyId', 'clientName', 'clientPhone'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { propertyId, clientName, clientPhone, preferredDate, preferredTime } = input;
        
        return {
          success: true,
          confirmationNumber: 'VW' + Math.random().toString(36).substr(2, 6).toUpperCase(),
          scheduledFor: preferredDate && preferredTime ? `${preferredDate} at ${preferredTime}` : 'To be confirmed',
          message: `Viewing scheduled for ${clientName}. You will receive a confirmation call at ${clientPhone} within 24 hours.`
        };
      },
    }),

    tool({
      name: 'getMarketAnalysis',
      description: 'Provide market analysis for a specific area including average prices, trends, and investment potential.',
      parameters: {
        type: 'object',
        properties: {
          location: {
            type: 'string',
            description: 'The area or neighborhood to analyze',
          },
          propertyType: {
            type: 'string',
            enum: ['house', 'condo', 'townhouse', 'all'],
            description: 'Type of property for the analysis',
          },
        },
        required: ['location'],
        additionalProperties: false,
      },
      execute: async (input: any) => {
        const { location, propertyType = 'all' } = input;
        
        return {
          location,
          propertyType,
          averagePrice: 425000,
          priceRange: { min: 280000, max: 750000 },
          marketTrend: 'increasing',
          priceChange6Months: '+5.2%',
          priceChange1Year: '+8.7%',
          averageDaysOnMarket: 22,
          inventoryLevel: 'moderate',
          investmentRating: 'good',
          keyFactors: [
            'Growing tech industry in the area',
            'New shopping center under construction',
            'Excellent school district ratings',
            'Easy access to public transportation'
          ]
        };
      },
    }),
  ],

  handoffs: [],
});

// Export the scenario as an array (following the pattern from other configs)
export const realEstateBrokerScenario = [realEstateBrokerAgent];

// Export the company name (used by guardrails and UI)
export const realEstateCompanyName = 'Premier Properties Group';
